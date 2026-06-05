import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import NLQueryRequest, SQLAnalyzeRequest
from database import execute_query
from llm import generate_sql
from analyzer import analyze_sql

app = FastAPI(
    title="QueryLens API",
    description="LLM-powered SQL analyzer and natural language to SQL engine: Performance Booster",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "QueryLens", "version": "1.0.0"}


@app.post("/api/nl-to-sql")
async def natural_language_to_sql(request: NLQueryRequest):
    start = time.time()
    try:
        sql = await generate_sql(request.question)
        results = await execute_query(sql)
        analysis = analyze_sql(sql)
        return {
            "question": request.question,
            "generated_sql": sql,
            "results": results,
            "analysis": analysis,
            "execution_time_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-sql")
async def analyze_existing_sql(request: SQLAnalyzeRequest):
    return analyze_sql(request.sql)


@app.post("/api/run-sql")
async def run_sql(request: SQLAnalyzeRequest):
    return await execute_query(request.sql)


# Serve the frontend HTML/CSS/JS files
frontend_dir = "/app/frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")