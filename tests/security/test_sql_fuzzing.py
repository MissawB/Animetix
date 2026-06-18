import pytest

from backend.core.utils.sql_guard import validate_sql_query

FUZZ_PAYLOADS = [
    # 1. CTE / WITH bypass attempts
    "WITH cte AS (UPDATE auth_user SET is_staff=true RETURNING *) SELECT * FROM animetix_mediaitem",
    "WITH cte AS (SELECT pg_sleep(10)) SELECT * FROM animetix_mediaitem",
    # 2. Set operations bypass
    "SELECT * FROM animetix_mediaitem EXCEPT SELECT * FROM auth_user",
    "SELECT * FROM animetix_mediaitem INTERSECT SELECT * FROM auth_user",
    # 3. String & Comment obfuscation
    "SELECT * FROM animetix_mediaitem WHERE title = $quote$ admin' -- $quote$",
    "SELECT /*+ bypass */ * FROM animetix_mediaitem",
    "SELECT * FROM animetix_mediaitem WHERE title = U&'\\0027' OR 1=1",
    # 4. System / Admin function execution
    "SELECT current_setting('is_superuser') FROM animetix_mediaitem",
    "SELECT version() FROM animetix_mediaitem",
    "SELECT set_config('role', 'postgres', false) FROM animetix_mediaitem",
    # 5. Multiple statements obfuscation
    "SELECT * FROM animetix_mediaitem\\g EXECUTE admin_payload",
    # 6. Deep nesting DoS
    "SELECT * FROM (" * 50 + "animetix_mediaitem" + ")" * 50,
]


@pytest.mark.parametrize("payload", FUZZ_PAYLOADS)
def test_sql_guard_rejects_complex_injections(payload):
    # All these payloads should be REJECTED (return False)
    assert validate_sql_query(payload) is False


def test_sql_guard_accepts_valid_complex_queries():
    valid_queries = [
        "SELECT id, title FROM animetix_mediaitem WHERE release_year = 2023",
        "SELECT COUNT(*) FROM animetix_mediaitem WHERE rating > 8.0",
        "SELECT LOWER(title) FROM animetix_mediaitem WHERE title LIKE '%naruto%'",
        "SELECT MAX(popularity) FROM animetix_mediaitem",
    ]
    for q in valid_queries:
        assert validate_sql_query(q) is True
