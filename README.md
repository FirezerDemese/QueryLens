# QueryLens

Two tools for working with SQL, in one small FastAPI app.

**Ask** takes a question in plain English, sends it to an LLM along with the
database schema, runs the SQL that comes back against a live PostgreSQL
database, and shows you both the query and the rows.

**Analyze** takes a query you already have and checks it against nine rules for
the patterns that stop an index being used. It returns a score out of 100, a
letter grade, and for every finding, what is wrong and what to write instead.

Live at <https://querylens-cudj.onrender.com>. It runs on Render's free tier, so
the first request after an idle period takes a few seconds to wake the service.

## The analyzer rules

| Code | Severity | Catches |
| --- | --- | --- |
| `FUNCTION_ON_COLUMN` | critical | `YEAR(col) = 2024` and friends, which prevent an index seek |
| `LEADING_WILDCARD` | critical | `LIKE '%value'`, which forces a scan |
| `POSSIBLE_CARTESIAN_JOIN` | critical | comma-separated tables with no join predicate |
| `SELECT_STAR` | warning | `SELECT *` |
| `UNBOUNDED_QUERY` | warning | no `WHERE`, no `LIMIT`, no aggregate |
| `NOT_IN_SUBQUERY` | warning | `NOT IN (SELECT ...)`, which is slow and breaks on NULLs |
| `SELECT_DISTINCT` | info | `DISTINCT` used to paper over a join that fans out |
| `IMPLICIT_TYPE_CONVERSION` | info | a numeric column compared to a quoted string |
| `MULTIPLE_OR_CONDITIONS` | info | three or more `OR`s in one predicate |

The rules are plain regex in `backend/analyzer.py`, deliberately. The scoring is
deterministic, so the same query always gets the same grade. The LLM is only
involved in generating SQL from English, never in judging it.

## Stack

Python, FastAPI, asyncpg, PostgreSQL 15, sqlglot, Groq (`llama-3.1-8b-instant`),
Docker. The frontend is plain HTML, CSS and JavaScript with no build step.

## Running it

You need Docker and a [Groq API key](https://console.groq.com).

```
echo "GROQ_API_KEY=your_key_here" > .env
docker compose up --build
```

Compose starts PostgreSQL, applies `database/schema.sql` and `database/seed.sql`
on first boot, and brings up the API. The app is on <http://localhost:8000> and
the generated API docs are on <http://localhost:8000/docs>.

The sample database has five tables: `customers`, `products`, `orders`,
`order_items` and `employees`.

## Endpoints

| Method | Path | Does |
| --- | --- | --- |
| `GET` | `/api/health` | health check |
| `POST` | `/api/nl-to-sql` | question in, generated SQL and its results out |
| `POST` | `/api/analyze-sql` | SQL in, score, grade and findings out |
| `POST` | `/api/run-sql` | executes a query and returns the rows |
