import re
from typing import Dict, Any


def analyze_sql(sql: str) -> Dict[str, Any]:
    issues = []
    score = 100
    sql_upper = sql.upper().strip()

    # Rule 1: SELECT *
    if re.search(r'SELECT\s+\*', sql_upper):
        issues.append({
            "severity": "warning", "code": "SELECT_STAR",
            "message": "SELECT * retrieves all columns including unnecessary ones.",
            "fix": "Specify only the columns you need."
        })
        score -= 15

    # Rule 2: Function on column in WHERE (destroys index performance)
    if re.search(r'WHERE.*?\b(YEAR|MONTH|DAY|UPPER|LOWER|TRIM|DATE_TRUNC)\s*\(', sql, re.IGNORECASE | re.DOTALL):
        issues.append({
            "severity": "critical", "code": "FUNCTION_ON_COLUMN",
            "message": "Function applied to a column in WHERE prevents index usage, causing a full table scan.",
            "fix": "Use a range condition instead. Example: WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'"
        })
        score -= 30

    # Rule 3: Leading wildcard LIKE
    if re.search(r"LIKE\s+'%[^']", sql_upper):
        issues.append({
            "severity": "critical", "code": "LEADING_WILDCARD",
            "message": "Leading wildcard in LIKE forces a full table scan.",
            "fix": "Use a trailing wildcard ('value%') or PostgreSQL full-text search."
        })
        score -= 25

    # Rule 4: No WHERE and no LIMIT on non-aggregate query
    has_where = bool(re.search(r'\bWHERE\b', sql_upper))
    has_limit = bool(re.search(r'\bLIMIT\b', sql_upper))
    has_agg = bool(re.search(r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\(', sql_upper))
    if not has_where and not has_limit and not has_agg:
        issues.append({
            "severity": "warning", "code": "UNBOUNDED_QUERY",
            "message": "No WHERE clause or LIMIT. This may return the entire table.",
            "fix": "Add a WHERE clause or LIMIT to restrict results."
        })
        score -= 10

    # Rule 5: NOT IN with subquery
    if re.search(r'\bNOT\s+IN\s*\(\s*SELECT', sql_upper):
        issues.append({
            "severity": "warning", "code": "NOT_IN_SUBQUERY",
            "message": "NOT IN with a subquery is slow and fails silently when the subquery returns NULLs.",
            "fix": "Replace with NOT EXISTS (SELECT 1 FROM ... WHERE ...). Safer and faster."
        })
        score -= 15

    # Rule 6: Implicit type conversion
    if re.search(r"WHERE\s+\w+\s*=\s*'\d+'", sql):
        issues.append({
            "severity": "info", "code": "IMPLICIT_TYPE_CONVERSION",
            "message": "Numeric column compared to a quoted string causes implicit type conversion.",
            "fix": "Remove quotes: WHERE customer_id = 42 not WHERE customer_id = '42'"
        })
        score -= 8

    # Rule 7: Multiple OR conditions
    if len(re.findall(r'\bOR\b', sql_upper)) >= 3:
        issues.append({
            "severity": "info", "code": "MULTIPLE_OR_CONDITIONS",
            "message": "Multiple OR conditions can prevent optimal index usage.",
            "fix": "Consider UNION ALL or IN() instead of multiple OR conditions."
        })
        score -= 5

    # Rule 8: Cartesian join risk
    from_match = re.search(r'FROM\s+([\w,\s]+?)(?:WHERE|ORDER|GROUP|LIMIT|$)', sql_upper, re.DOTALL)
    if from_match and ',' in from_match.group(1) and 'JOIN' not in sql_upper:
        issues.append({
            "severity": "critical", "code": "POSSIBLE_CARTESIAN_JOIN",
            "message": "Multiple tables in FROM without explicit JOIN may produce a cartesian product.",
            "fix": "Use explicit JOIN ... ON syntax."
        })
        score -= 30

    # Rule 9: SELECT DISTINCT overuse
    if 'SELECT DISTINCT' in sql_upper:
        issues.append({
            "severity": "info", "code": "SELECT_DISTINCT",
            "message": "DISTINCT forces a sort and dedup pass. Often signals a JOIN issue.",
            "fix": "Check if a JOIN is producing duplicates. Fixing the JOIN is more efficient."
        })
        score -= 5

    score = max(0, score)
    grade = 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'F'
    return {"score": score, "grade": grade, "issues": issues, "issue_count": len(issues)}