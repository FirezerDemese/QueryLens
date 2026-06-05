import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

DATABASE_SCHEMA = """
Database: QueryLens Demo (PostgreSQL)

Tables:

customers: customer_id (pk), first_name, last_name, email, city, country, created_date
products: product_id (pk), product_name, category (Electronics/Furniture/Books/Sports/Kitchen), price, stock_quantity
orders: order_id (pk), customer_id (fk->customers), order_date, total_amount, status (completed/pending)
order_items: item_id (pk), order_id (fk->orders), product_id (fk->products), quantity, unit_price
employees: employee_id (pk), first_name, last_name, department (Engineering/Data/Product), salary, hire_date, manager_id (self-ref fk)
"""

async def execute_query(sql: str) -> dict:
    if not sql.strip().upper().startswith("SELECT"):
        return {"columns": [], "rows": [], "count": 0,
                "error": "Only SELECT queries are permitted."}
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch(sql.strip())
        if not rows:
            return {"columns": [], "rows": [], "count": 0, "error": None}
        columns = list(rows[0].keys())
        data = []
        for row in rows[:100]:
            row_dict = {}
            for k, v in dict(row).items():
                row_dict[k] = v.isoformat() if hasattr(v, 'isoformat') else v
            data.append(row_dict)
        return {"columns": columns, "rows": data, "count": len(data), "error": None}
    except Exception as e:
        return {"columns": [], "rows": [], "count": 0, "error": str(e)}
    finally:
        if conn:
            await conn.close()