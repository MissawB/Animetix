# -*- coding: utf-8 -*-
import logging
import os
import sys

# Configurer le logging pour voir les alertes du guardrail
logging.basicConfig(level=logging.WARNING)

# Ajouter le chemin du backend
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from core.utils.sql_guard import validate_sql_query  # noqa: E402


def run_audit():
    print("🚀 Starting Formal Security Audit for SQL Guard...\n")

    test_cases = [
        # --- BASIC SAFE QUERIES ---
        ("SELECT * FROM animetix_mediaitem LIMIT 10", True, "Basic SELECT with LIMIT"),
        (
            "SELECT count(*) FROM animetix_mediaitem WHERE popularity > 10 LIMIT 1",
            True,
            "SELECT with WHERE, COUNT and LIMIT",
        ),
        (
            "SELECT lower(title) FROM animetix_mediaitem LIMIT 50",
            True,
            "SELECT with whitelisted function and LIMIT",
        ),
        # --- FORBIDDEN OPERATIONS ---
        (
            "INSERT INTO animetix_mediaitem (title) VALUES ('Hacked') LIMIT 1",
            False,
            "INSERT attempt",
        ),
        ("DROP TABLE animetix_mediaitem", False, "DROP attempt"),
        ("DELETE FROM animetix_mediaitem LIMIT 1", False, "DELETE attempt"),
        (
            "UPDATE animetix_mediaitem SET title='Hacked' LIMIT 1",
            False,
            "UPDATE attempt",
        ),
        (
            "SELECT * FROM animetix_mediaitem LIMIT 1; DROP TABLE users;",
            False,
            "Multiple statements (Semicolon injection)",
        ),
        # --- TABLE WHITELIST BYPASS ATTEMPTS ---
        ("SELECT * FROM users LIMIT 10", False, "Unauthorized table"),
        (
            "SELECT * FROM animetix_mediaitem JOIN users ON 1=1 LIMIT 10",
            False,
            "JOIN with unauthorized table",
        ),
        (
            "SELECT * FROM (SELECT * FROM users) as sub LIMIT 10",
            False,
            "Subquery with unauthorized table",
        ),
        (
            "SELECT * FROM animetix_mediaitem, users LIMIT 10",
            False,
            "Implicit join with unauthorized table",
        ),
        # --- COMMENT INJECTIONS ---
        ("SELECT * FROM animetix_mediaitem -- comment LIMIT 10", False, "Line comment"),
        (
            "SELECT * FROM animetix_mediaitem /* multi-line \n comment */ LIMIT 10",
            False,
            "Multi-line comment",
        ),
        # --- UNION & SET OPERATIONS ---
        (
            "SELECT title FROM animetix_mediaitem UNION SELECT username FROM users LIMIT 10",
            False,
            "UNION injection",
        ),
        (
            "SELECT title FROM animetix_mediaitem EXCEPT SELECT username FROM users LIMIT 10",
            False,
            "EXCEPT injection",
        ),
        # --- DANGEROUS FUNCTIONS ---
        (
            "SELECT pg_sleep(10) FROM animetix_mediaitem LIMIT 1",
            False,
            "pg_sleep (Time-based DoS)",
        ),
        (
            "SELECT current_setting('is_superuser') FROM animetix_mediaitem LIMIT 1",
            False,
            "Postgres settings access",
        ),
        (
            "SELECT version() FROM animetix_mediaitem LIMIT 1",
            False,
            "System information leak",
        ),
        (
            "SELECT substring(title from 1 for 1) FROM animetix_mediaitem LIMIT 1",
            False,
            "Substring (Exfiltration pattern)",
        ),
        # --- OBFUSCATION & DIALECT TRICKS ---
        (
            'SELECT "animetix_mediaitem".* FROM animetix_mediaitem LIMIT 10',
            True,
            "Quoted table name (Safe)",
        ),
        ('SELECT * FROM "Users" LIMIT 1', False, "Quoted unauthorized table"),
        (
            "WITH cte AS (SELECT * FROM users) SELECT * FROM cte LIMIT 1",
            False,
            "CTE bypass attempt",
        ),
        (
            "SELECT * FROM animetix_mediaitem WHERE title = 'foo' OR 1=1 LIMIT 100",
            True,
            "SQL Injection in value (Safe because it's still a SELECT on the same table)",
        ),
        # --- DOS & COMPLEXITY ---
        (
            "SELECT " + " + ".join(["1"] * 100) + " FROM animetix_mediaitem LIMIT 1",
            False,
            "DoS: Extremely wide expression",
        ),
        (
            "SELECT * FROM animetix_mediaitem "
            + " ".join(
                ["JOIN animetix_mediaitem as t" + str(i) + " ON 1=1" for i in range(25)]
            )
            + " LIMIT 1",
            False,
            "DoS: Deep AST/Complex Joins",
        ),
        # --- LIMIT CHECKS ---
        ("SELECT * FROM animetix_mediaitem", False, "Missing LIMIT"),
        ("SELECT * FROM animetix_mediaitem LIMIT 5000", False, "LIMIT too high"),
        ("SELECT * FROM animetix_mediaitem LIMIT 'not_an_int'", False, "Invalid LIMIT"),
        # --- EDGE CASES ---
        ("SELECT FROM animetix_mediaitem LIMIT 1", False, "Empty expressions"),
        ("", False, "Empty string"),
        (None, False, "None input"),
        ("SELECT 1 LIMIT 1", False, "SELECT without table"),
        (
            "SELECT * FROM animetix_mediaitem ORDER BY (SELECT 1 FROM users) LIMIT 1",
            False,
            "Subquery in ORDER BY",
        ),
    ]

    passed = 0
    failed = []

    for sql, expected, desc in test_cases:
        result = validate_sql_query(sql)
        if result == expected:
            passed += 1
            # print(f"✅ PASSED: {desc}")
        else:
            print(f"❌ FAILED: {desc}")
            print(f"   Query: {sql}")
            print(f"   Expected: {expected}, Got: {result}")
            failed.append(desc)

    print(f"\nSummary: {passed}/{len(test_cases)} tests passed.")

    if not failed:
        print("🎉 ALL TESTS PASSED. SQL Guard is robust against these patterns.")
    else:
        print(f"🚨 FOUND {len(failed)} POTENTIAL VULNERABILITIES.")
        sys.exit(1)


if __name__ == "__main__":
    run_audit()
