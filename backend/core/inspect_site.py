"""Safe homepage fetch (SSRF-guarded, size/time limited). stdlib only."""
import ipaddress, socket
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

MAX_BYTES = 1_500_000
UA = "Mozilla/5.0 (compatible; CodeCelixLeadFinder/1.0)"


def _safe_host(host):
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except OSError:
        return False


class _Guard(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme not in ("http", "https") or not _safe_host(urlparse(newurl).hostname or ""):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_homepage(url, timeout=8, allow_private=False):
    """Returns (status, html, final_url). status: ok | no_website | failed."""
    if not url:
        return "no_website", "", None
    if "://" not in url:
        url = "http://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return "failed", "", url
    if not allow_private and not _safe_host(p.hostname):
        return "failed", "", url
    try:
        opener = build_opener(_Guard)
        with opener.open(Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
            raw = r.read(MAX_BYTES)
            return "ok", raw.decode(r.headers.get_content_charset() or "utf-8", "replace"), r.geturl()
    except Exception:
        return "failed", "", url
