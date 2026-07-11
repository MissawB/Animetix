"""Liveness endpoint backing the deploy smoke test (ci.yml deploy-to-prod).

Plain Django view by design: no DRF (so the anon throttle can never 429 the
deploy gate), no auth, no DB query. If it answers 200, the revision booted —
supervisord runs migrate before starting gunicorn, so a failed migration or
missing secret never reaches this point.
"""


def test_healthz_returns_200_anonymously(client):
    res = client.get("/healthz/")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "revision" in body


def test_healthz_is_not_throttled(client):
    # Plain Django view: 30 rapid anonymous hits must all pass (a DRF view
    # would eat the anon rate limit and 429 mid-deploy).
    codes = {client.get("/healthz/").status_code for _ in range(30)}
    assert codes == {200}
