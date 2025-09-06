from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="RAG System API", version="1.0.0")

# Mount static files only if directory exists
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float

class Course(BaseModel):
    id: str
    title: str
    description: str
    category: str

@app.get("/")
async def root():
    return {"message": "RAG System API", "status": "active"}

@app.post("/api/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    # Mock RAG response for testing
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    return QueryResponse(
        answer=f"Mock answer for: {request.query}",
        sources=["source1.pdf", "source2.pdf"],
        confidence=0.85
    )

@app.get("/api/courses", response_model=List[Course])
async def get_courses():
    # Mock courses data
    return [
        Course(id="1", title="Machine Learning Basics", description="Introduction to ML", category="AI"),
        Course(id="2", title="Deep Learning", description="Neural networks and deep learning", category="AI"),
        Course(id="3", title="Data Science", description="Data analysis and visualization", category="Data")
    ]

@app.get("/api/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    courses = {
        "1": Course(id="1", title="Machine Learning Basics", description="Introduction to ML", category="AI"),
        "2": Course(id="2", title="Deep Learning", description="Neural networks and deep learning", category="AI"),
        "3": Course(id="3", title="Data Science", description="Data analysis and visualization", category="Data")
    }
    
    if course_id not in courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return courses[course_id]