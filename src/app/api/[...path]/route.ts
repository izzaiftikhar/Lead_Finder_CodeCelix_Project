// Server-side proxy to FastAPI. BACKEND_API_URL / BACKEND_API_KEY and the session token never reach page JavaScript:
// the session lives in an httpOnly cookie that this route converts to a Bearer token.
export const maxDuration = 60;

const COOKIE = "lf_session";
const UUID = "[0-9a-f-]{36}";
const ALLOWED = new RegExp(
  `^(health|auth/(login|register|logout|me)|markets|markets/[A-Z]{2}/cities|estimate|jobs|jobs/${UUID}(/(leads|cancel|resume|rerun|export))?` +
    `|leads/${UUID}/(feedback|save)|saved|stats|admin/(config|country-niches|niche-keywords|chatbot-signatures|limits|suppression|cost)` +
    `|admin/(niche-keywords|chatbot-signatures)/\\d+)$`,
);

function cookieValue(req: Request, name: string): string | null {
  const m = (req.headers.get("cookie") || "").split(/;\s*/).find((c) => c.startsWith(name + "="));
  return m ? decodeURIComponent(m.slice(name.length + 1)) : null;
}

function setCookie(req: Request, value: string, maxAge: number): string {
  const secure = new URL(req.url).protocol === "https:" || req.headers.get("x-forwarded-proto") === "https";
  return `${COOKIE}=${encodeURIComponent(value)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${secure ? "; Secure" : ""}`;
}

async function proxy(req: Request, ctx: { params: Promise<{ path: string[] }> }): Promise<Response> {
  const base = (process.env.BACKEND_API_URL || "").replace(/\/+$/, "");
  if (!base) return Response.json({ detail: "BACKEND_API_URL is not configured on the frontend deployment." }, { status: 500 });

  const path = (await ctx.params).path.join("/");
  if (!ALLOWED.test(path)) return Response.json({ detail: "Not found" }, { status: 404 });

  const url = new URL(req.url);
  const origin = req.headers.get("origin");
  if (req.method !== "GET" && origin && new URL(origin).host !== url.host) return Response.json({ detail: "Cross-origin request blocked" }, { status: 403 });

  const headers: Record<string, string> = {};
  const ct = req.headers.get("content-type");
  if (ct) headers["content-type"] = ct;
  const idem = req.headers.get("idempotency-key");
  if (idem) headers["idempotency-key"] = idem;
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) headers["x-forwarded-for"] = fwd;
  if (process.env.BACKEND_API_KEY) headers["x-api-key"] = process.env.BACKEND_API_KEY;
  const token = cookieValue(req, COOKIE);
  if (token) headers["authorization"] = `Bearer ${token}`;

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const upstream = await fetch(`${base}/api/${path}${url.search}`, {
      method: req.method, headers, body: req.method === "GET" || req.method === "DELETE" ? undefined : await req.text(),
      signal: ctrl.signal, cache: "no-store",
    });

    if ((path === "auth/login" || path === "auth/register") && upstream.ok) {
      const data = (await upstream.json()) as { token: string; user: unknown };
      return new Response(JSON.stringify({ user: data.user }), {
        status: 200, headers: { "content-type": "application/json", "set-cookie": setCookie(req, data.token, 14 * 24 * 3600) },
      });
    }
    const out = new Headers();
    for (const h of ["content-type", "content-disposition"]) { const v = upstream.headers.get(h); if (v) out.set(h, v); }
    if (path === "auth/logout") out.set("set-cookie", setCookie(req, "", 0));
    return new Response(upstream.body, { status: upstream.status, headers: out });
  } catch (e) {
    const timeout = e instanceof Error && e.name === "AbortError";
    return Response.json({ detail: timeout ? "The backend took too long to respond." : "The backend is unreachable." }, { status: timeout ? 504 : 502 });
  } finally { clearTimeout(timer); }
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as DELETE };
