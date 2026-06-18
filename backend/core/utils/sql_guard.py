import logging

from sqlglot import ParseError, exp, parse

logger = logging.getLogger("animetix.sql_guard")


def validate_sql_query(sql: str) -> bool:
    """
    Vérifie la sécurité d'une requête SQL générée par IA en utilisant un parseur SQL robuste.
    Retourne True si et seulement si la requête est un SELECT inoffensif ciblant uniquement animetix_mediaitem.
    """
    if not sql or not isinstance(sql, str):
        return False

    sql_clean = sql.strip()

    # Re-introduce check for SQL comments to prevent comment-based injection
    if "--" in sql_clean or "/*" in sql_clean:
        logger.warning("SQL Guardrail: SQL comments detected, which are forbidden.")
        return False

    try:
        # Parse the SQL query with PostgreSQL dialect
        parsed_statements = parse(sql_clean, read="postgres")

        # Ensure only one statement is present
        if len(parsed_statements) != 1:
            logger.warning(
                f"SQL Guardrail: Multiple statements detected in query: {sql_clean[:200]}"
            )
            return False

        parsed_sql = parsed_statements[0]

        # AST Depth Check to prevent DoS via deep nesting or complex recursions
        def get_depth(node, current_depth=0):
            if current_depth > 50:
                # Fail-safe
                raise ValueError("AST too deep")
            max_depth = current_depth
            # Use args to traverse child nodes
            if hasattr(node, "args"):
                for k, v in node.args.items():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, exp.Expression):
                                max_depth = max(
                                    max_depth, get_depth(item, current_depth + 1)
                                )
                    elif isinstance(v, exp.Expression):
                        max_depth = max(max_depth, get_depth(v, current_depth + 1))
            return max_depth

        try:
            if get_depth(parsed_sql) > 20:
                logger.warning("SQL Guardrail: Query AST is too deep (DoS protection).")
                return False
        except ValueError:
            return False

        # 1. Ensure it's a SELECT statement
        if not isinstance(parsed_sql, exp.Select):
            logger.warning(
                f"SQL Guardrail: Query is not a SELECT statement: {sql_clean[:200]}"
            )
            return False

        # 1.1 Ensure at least one expression is selected
        if not parsed_sql.expressions:
            logger.warning(
                f"SQL Guardrail: Empty SELECT expressions: {sql_clean[:200]}"
            )
            return False

        # 1.2 JOIN Limitation (Max 5 joins to prevent DoS)
        joins = list(parsed_sql.find_all(exp.Join))
        if len(joins) > 5:
            logger.warning(f"SQL Guardrail: Too many JOINs ({len(joins)}) detected.")
            return False

        # 1.3 MANDATORY LIMIT Check (Prevent massive data exfiltration/DoS)
        limit_node = parsed_sql.args.get("limit")
        if not limit_node:
            logger.warning(
                "SQL Guardrail: Missing LIMIT clause. Queries must have a LIMIT."
            )
            return False

        try:
            limit_val = int(limit_node.expression.this)
            if limit_val > 1000:
                logger.warning(
                    f"SQL Guardrail: LIMIT too high ({limit_val}). Max allowed is 1000."
                )
                return False
        except (ValueError, AttributeError):
            logger.warning("SQL Guardrail: Invalid or non-static LIMIT clause.")
            return False

        # 2. Check for forbidden operations (DDL, DML, and dangerous extensions)
        # Use a list of types and convert to tuple later
        forbidden_expressions = [
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.AlterTable,
            exp.Create,
            exp.Merge,
            exp.Show,
            exp.Set,
            exp.Copy,
            exp.Command,
            exp.Commit,
            exp.Rollback,
            exp.Transaction,
            exp.Kill,
            exp.Union,
            exp.Except,
            exp.Intersect,
            # Block bitwise operations often used in obfuscation
            exp.BitwiseAnd,
            exp.BitwiseOr,
            exp.BitwiseXor,
            exp.BitwiseNot,
            exp.BitwiseLeftShift,
            exp.BitwiseRightShift,
        ]

        # Safely add potentially missing types
        for extra_type in [
            "TruncateTable",
            "Explain",
            "Analyze",
            "Pragma",
            "Fetch",
            "Into",
            "LoadData",
        ]:
            if hasattr(exp, extra_type):
                forbidden_expressions.append(getattr(exp, extra_type))

        forbidden_tuple = tuple(forbidden_expressions)

        for node in parsed_sql.walk():
            if isinstance(node, forbidden_tuple):
                logger.warning(
                    f"SQL Guardrail: Forbidden operation '{node.key}' detected in query: {sql_clean[:200]}"
                )
                return False

        # 2.1. Function Whitelisting: Allow ONLY specific safe functions
        # Added common text and math functions needed for catalog queries
        # Note: SUBSTRING removed as it was used in original tests to represent 'dangerous' inference patterns
        allowed_functions = {
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "lower",
            "upper",
            "length",
            "trim",
            "coalesce",
            "cast",
            "round",
        }
        for func_exp in parsed_sql.find_all(exp.Func):
            # Use .key for function name as .name is empty for specialized classes like Lower/Upper
            func_name = func_exp.key.lower() if func_exp.key else ""

            # Allow COUNT(*) specifically
            if (
                isinstance(func_exp, exp.Count)
                and func_exp.this
                and isinstance(func_exp.this, exp.Star)
            ):
                continue

            # Allow CAST, CASE, and IF expressions even if they inherit from Func
            if isinstance(func_exp, (exp.Cast, exp.Case, exp.If)):
                continue

            if func_name not in allowed_functions:
                logger.warning(
                    f"SQL Guardrail: Forbidden function '{func_name}' detected in query: {sql_clean[:200]}"
                )
                return False

        # 3. Table Whitelisting: Ensure ONLY 'animetix_mediaitem' table is accessed
        allowed_table = "animetix_mediaitem"
        found_tables = set()
        for table_exp in parsed_sql.find_all(exp.Table):
            table_name = table_exp.name.lower()
            found_tables.add(table_name)

        if not found_tables:
            logger.warning(
                f"SQL Guardrail: No tables found in SELECT query: {sql_clean[:200]}"
            )
            return False

        # Strict check: exactly one table allowed, and it must be the whitelist one
        if len(found_tables) > 1 or list(found_tables)[0] != allowed_table:
            logger.warning(
                f"SQL Guardrail: Query accesses forbidden tables: {found_tables}. Only '{allowed_table}' is allowed. Query: {sql_clean[:200]}"
            )
            return False

        return True

    except ParseError as e:
        logger.warning(
            f"SQL Guardrail: SQL parsing error: {e} in query: {sql_clean[:200]}"
        )
        return False
    except Exception as e:
        logger.error(
            f"SQL Guardrail: An unexpected error occurred: {e} in query: {sql_clean[:200]}"
        )
        return False
