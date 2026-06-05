import os
from groq import AsyncGroq
from dotenv import load_dotenv
from database import DATABASE_SCHEMA

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT_TEMPLATE = """You are an expert PostgreSQL database engineer.
Generate ONLY the SQL query. No markdown. No backticks. No explanation. Just SQL.

{schema}

Rules:
- PostgreSQL syntax only (use LIMIT not TOP)
- Never use SELECT * - always name the columns
- Use table aliases in JOINs

Question: {question}"""


async def generate_sql(question: str) -> str:
    prompt = PROMPT_TEMPLATE.format(schema=DATABASE_SCHEMA, question=question)

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    sql = response.choices[0].message.content.strip()

    # Clean up accidental markdown fences
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(l for l in lines if not l.startswith("```")).strip()

    return sql
