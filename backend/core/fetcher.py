"""HTTP fetcher: SSRF-guarded, robots.txt aware, size/time limited. Returns FetchResult; never raises."""
import ipaddress, socket, urllib.robotparser
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from .config import settings

MAX_BYTES = 1_500_000


def user_agent():
    c = settings.ABUSE_CONTACT
    return "CodeCelixLeadFinder/1.0" + (f" (+{c})" if c else "")


@dataclass
class FetchResult:
    status: str          # ok | blocked | down | timeout | disallowed
    code: int = 0
    html: str = ""
    final_url: str = ""
    reason: str = ""


def _safe_host(host):
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
                return False
        return True
    except OSError:
        return None  # DNS failure


class _Guard(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urlparse(newurl)
        if p.scheme not in ("http", "https") or _safe_host(p.hostname or "") is not True:
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_robots = {}


def _allowed(url):
    if not settings.ROBOTS_ENABLED:
        return True
    p = urlparse(url)
    key = f"{p.scheme}://{p.netloc}"
    rp = _robots.get(key)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = Request(key + "/robots.txt", headers={"User-Agent": user_agent()})
            with build_opener(_Guard).open(req, timeout=8) as r:
                rp.parse(r.read(200_000).decode("utf-8", "replace").splitlines())
        except HTTPError as e:
            rp.parse([]) if e.code in (401, 403, 404) or e.code >= 500 else rp.parse([])
        except Exception:
            rp.parse([])
        _robots[key] = rp
    return rp.can_fetch(user_agent(), url)


def fetch_page(url, allow_private=False):
    if not url:
        return FetchResult("down", reason="no url")
    if "://" not in url:
        url = "http://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return FetchResult("down", reason="bad url")
    if not allow_private:
        safe = _safe_host(p.hostname)
        if safe is None:
            return FetchResult("down", reason="DNS failure")
        if safe is False:
            return FetchResult("blocked", reason="private address blocked")
    if not allow_private and not _allowed(url):
        return FetchResult("disallowed", reason="robots.txt disallows")
    try:
        with build_opener(_Guard).open(Request(url, headers={"User-Agent": user_agent(), "Accept": "text/html,*/*;q=0.8"}),
                                       timeout=settings.PAGE_TIMEOUT_SECS) as r:
            raw = r.read(MAX_BYTES)
            return FetchResult("ok", r.status, raw.decode(r.headers.get_content_charset() or "utf-8", "replace"), r.geturl())
    except HTTPError as e:
        if e.code in (401, 403, 429, 503):
            return FetchResult("blocked", e.code, reason=f"HTTP {e.code}")
        return FetchResult("down", e.code, reason=f"HTTP {e.code}")
    except (socket.timeout, TimeoutError):
        return FetchResult("timeout", reason="timeout")
    except URLError as e:
        return FetchResult("timeout" if isinstance(e.reason, (socket.timeout, TimeoutError)) else "down", reason=str(e.reason)[:80])
    except Exception as e:  # noqa
        return FetchResult("down", reason=type(e).__name__)
