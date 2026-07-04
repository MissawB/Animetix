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

// Firebase Auth reserves the /__/auth/** and /__/firebase/** paths (OAuth
// handler, email action links, SDK init config). They live on the Firebase
// auth domain, not on our Cloud Run app, so we proxy them straight to Firebase.
// This lets VITE_FIREBASE_AUTH_DOMAIN be animetix.xyz — sign-in popups and
// email verification links then stay on the custom domain instead of
// animetix.firebaseapp.com.
const FIREBASE_AUTH_HOST = "animetix.firebaseapp.com";

const isFirebaseReservedPath = (pathname) =>
  pathname.startsWith("/__/auth/") || pathname.startsWith("/__/firebase/");

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const visitorHost = url.host; // animetix.xyz (or www.animetix.xyz)

    // Firebase reserved paths → proxy to the Firebase auth domain untouched.
    // fetch derives the Host header from the URL, so Firebase sees its own host.
    if (isFirebaseReservedPath(url.pathname)) {
      url.protocol = "https:";
      url.hostname = FIREBASE_AUTH_HOST;
      url.port = "";
      return fetch(new Request(url, request));
    }

    url.protocol = "https:";
    url.hostname = ORIGIN_HOST;
    url.port = "";

    const req = new Request(url, request);
    req.headers.set("X-Forwarded-Host", visitorHost);
    req.headers.set("X-Forwarded-Proto", "https");

    return fetch(req);
  },
};
