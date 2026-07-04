// Cloudflare Worker reverse-proxy for animetix.xyz -> Cloud Run.
//
// Cloud Run routes requests by the HTTP Host header and only recognises its own
// *.run.app hostname. Cloudflare (free plan) cannot rewrite the Host header via
// Origin Rules (Enterprise-only) and europe-west9 has no Cloud Run domain
// mapping, so this Worker rewrites the destination hostname to the run.app URL.
//
// The visitor keeps seeing animetix.xyz; only the Host sent to the origin changes.
// We always talk to the origin over HTTPS and forward X-Forwarded-Host /
// X-Forwarded-Proto so Django (USE_X_FORWARDED_HOST=True) builds animetix.xyz
// absolute URLs and never SSL-redirects to the run.app host. Method, headers,
// body, cookies and WebSocket upgrades are passed through as-is.
const ORIGIN_HOST = "animetix-web-zhwkba45ta-od.a.run.app";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const visitorHost = url.host; // animetix.xyz (or www.animetix.xyz)

    url.protocol = "https:";
    url.hostname = ORIGIN_HOST;
    url.port = "";

    const req = new Request(url, request);
    req.headers.set("X-Forwarded-Host", visitorHost);
    req.headers.set("X-Forwarded-Proto", "https");

    return fetch(req);
  },
};
