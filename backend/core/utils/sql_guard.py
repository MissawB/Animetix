import logging
from sqlglot import parse, exp, ParseError # Changed parse_one to parse

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
        # Use sqlglot.parse to get a list of expressions
        parsed_statements = parse(sql_clean, read="postgres")

        # Ensure only one statement is present
        if len(parsed_statements) != 1:
            logger.warning(f"SQL Guardrail: Multiple statements detected in query: {sql_clean[:200]}")
            return False

        parsed_sql = parsed_statements[0]
        print(f"DEBUG: Parsed SQL for invalid syntax: {parsed_sql.dump()}")

        # 1. Ensure it's a SELECT statement
        if not isinstance(parsed_sql, exp.Select):
            logger.warning(f"SQL Guardrail: Query is not a SELECT statement: {sql_clean[:200]}")
            return False

        # 2. Check for forbidden operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.)
        forbidden_expressions = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.AlterTable, exp.Create,
            exp.Merge, exp.Show, exp.Set,
            exp.Copy, exp.Command
        )
        for node in parsed_sql.walk(): # Traverse the AST
            if isinstance(node, forbidden_expressions):
                logger.warning(f"SQL Guardrail: Forbidden operation '{node.key}' detected in query: {sql_clean[:200]}")
                return False
            # Prevent UNION as it can be used for injection (e.g., UNION SELECT sensitive_data)
            if isinstance(node, exp.Union):
                logger.warning(f"SQL Guardrail: UNION detected in query, which is forbidden: {sql_clean[:200]}")
                return False

        # 2.1. Function Whitelisting: Allow only safe aggregate functions
        allowed_functions = {"count", "sum", "avg", "min", "max"} # Lowercased for comparison
        for func_exp in parsed_sql.find_all(exp.Func):
            func_name = func_exp.name.lower()

            # Allow COUNT(*) specifically when it's exp.Count with exp.Star as its argument
            if isinstance(func_exp, exp.Count) and func_exp.this and isinstance(func_exp.this, exp.Star):
                continue

            if func_name not in allowed_functions:
                logger.warning(f"SQL Guardrail: Forbidden function '{func_name}' detected in query: {sql_clean[:200]}")
                return False
            
        # 3. Table Whitelisting: Ensure only 'animetix_mediaitem' table is accessed
        allowed_table = "animetix_mediaitem"
        found_tables = set()
        for table_exp in parsed_sql.find_all(exp.Table):
            table_name = table_exp.name.lower() # Normalize to lower case for comparison
            found_tables.add(table_name)
        
        if not found_tables:
            logger.warning(f"SQL Guardrail: No tables found in SELECT query: {sql_clean[:200]}")
            return False

        if len(found_tables) > 1 or (len(found_tables) == 1 and allowed_table not in found_tables):
            logger.warning(f"SQL Guardrail: Query accesses forbidden tables: {found_tables}. Only '{allowed_table}' is allowed. Query: {sql_clean[:200]}")
            return False
            
        # Ensure that the only table found is the allowed_table
        if found_tables and list(found_tables)[0] != allowed_table:
            logger.warning(f"SQL Guardrail: Query accesses forbidden tables: {found_tables}. Only '{allowed_table}' is allowed. Query: {sql_clean[:200]}")
            return False

        # All checks passed
        return True

    except ParseError as e:
        logger.warning(f"SQL Guardrail: SQL parsing error (malformed or disallowed syntax): {e} in query: {sql_clean[:200]}")
        return False
    except Exception as e:
        logger.error(f"SQL Guardrail: An unexpected error occurred during SQL validation: {e} in query: {sql_clean[:200]}")
        return False
