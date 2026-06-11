import pytest
from backend.core.utils.sql_guard import validate_sql_query

# Test cases for valid SELECT queries targeting 'animetix_mediaitem'
@pytest.mark.parametrize("valid_sql", [
    "SELECT * FROM animetix_mediaitem;",
    "SELECT id, name FROM animetix_mediaitem WHERE id = 1;",
    "SELECT name FROM animetix_mediaitem ORDER BY name DESC;",
    "SELECT COUNT(*) FROM animetix_mediaitem WHERE category = 'Movie';",
    "SELECT DISTINCT genre FROM animetix_mediaitem;",
    "SELECT column_name FROM animetix_mediaitem LIMIT 10 OFFSET 5;",
    "SELECT A.id, A.name FROM animetix_mediaitem AS A WHERE A.id > 100;",
])
def test_valid_select_query(valid_sql):
    assert validate_sql_query(valid_sql) is True

# Test cases for invalid SQL syntax
@pytest.mark.parametrize("invalid_syntax_sql", [
    "SELECT FROM animetix_mediaitem;",
    "SELECT id, FROM animetix_mediaitem;",
    "SELECT * FROM WHERE id = 1;",
    "SELECT * FROM animetix_mediaitem WHERE ;",
    "SELECT * animetix_mediaitem;",
    "INVALID SELECT * FROM animetix_mediaitem;",
])
def test_invalid_sql_syntax(invalid_syntax_sql):
    assert validate_sql_query(invalid_syntax_sql) is False

# Test cases for forbidden operations (DML, DDL, DCL, etc.)
@pytest.mark.parametrize("forbidden_operation_sql", [
    "INSERT INTO animetix_mediaitem (id, name) VALUES (1, 'Test');",
    "UPDATE animetix_mediaitem SET name = 'New Name' WHERE id = 1;",
    "DELETE FROM animetix_mediaitem WHERE id = 1;",
    "DROP TABLE animetix_mediaitem;",
    "TRUNCATE TABLE animetix_mediaitem;",
    "ALTER TABLE animetix_mediaitem ADD COLUMN new_col TEXT;",
    "CREATE TABLE new_table (id INT);",
    "UNION SELECT 1, 'abc';",  # UNION should be forbidden
    "SELECT 1 FROM animetix_mediaitem UNION SELECT 2 FROM another_table;",
    "GRANT SELECT ON animetix_mediaitem TO PUBLIC;",
    "REVOKE ALL ON animetix_mediaitem FROM PUBLIC;",
    "EXECUTE some_function();",
    "COPY animetix_mediaitem TO '/tmp/data.csv';",
    "VACUUM FULL;",
    "ANALYZE animetix_mediaitem;",
    "SELECT * FROM animetix_mediaitem; DELETE FROM users;" # Multiple statements
])
def test_forbidden_operations(forbidden_operation_sql):
    assert validate_sql_query(forbidden_operation_sql) is False

# Test cases for accessing forbidden tables
@pytest.mark.parametrize("forbidden_table_sql", [
    "SELECT * FROM auth_user;",
    "SELECT username FROM animetix_profile;",
    "SELECT * FROM django_session WHERE session_key = 'abc';",
    "SELECT * FROM animetix_mediaitem; SELECT * FROM auth_user;", # Chained select to forbidden table
    "SELECT T1.id FROM animetix_mediaitem AS T1 JOIN auth_user AS T2 ON T1.user_id = T2.id;"
])
def test_forbidden_tables(forbidden_table_sql):
    assert validate_sql_query(forbidden_table_sql) is False

# Test cases for SQL Injection attempts
@pytest.mark.parametrize("sql_injection_attempts", [
    "SELECT * FROM animetix_mediaitem WHERE id = 1 OR 1=1; --",
    "SELECT * FROM animetix_mediaitem WHERE id = 1; DROP TABLE users;",
    "SELECT * FROM animetix_mediaitem WHERE id = 1 AND SUBSTRING(password, 1, 1) = 'a';",
    "SELECT * FROM animetix_mediaitem WHERE id = 1; /* comment */ SELECT pg_sleep(5);",
    "SELECT * FROM animetix_mediaitem WHERE id = 1; SELECT @@version;",
    "SELECT * FROM animetix_mediaitem WHERE name LIKE '%test%' --';",
    "SELECT * FROM animetix_mediaitem WHERE id = 1; INSERT INTO users VALUES (1, 'admin');",
])
def test_sql_injection_attempts(sql_injection_attempts):
    assert validate_sql_query(sql_injection_attempts) is False

# Test cases for case insensitivity
@pytest.mark.parametrize("case_insensitive_sql", [
    "select * from animetix_mediaitem;",
    "SELECT * from animetix_mediaitem;",
    "select id from Animetix_MediaItem;",
])
def test_case_insensitivity(case_insensitive_sql):
    assert validate_sql_query(case_insensitive_sql) is True

# Test cases for empty or non-string input
@pytest.mark.parametrize("invalid_input", [
    None,
    "",
    123,
    [],
    {}
])
def test_invalid_input(invalid_input):
    assert validate_sql_query(invalid_input) is False
