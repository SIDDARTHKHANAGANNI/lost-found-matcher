from fastapi import FastAPI
from app.routers import items

app = FastAPI(title="Lost & Found Matcher API")

app.include_router(items.router, prefix="/items", tags=["items"])

@app.get("/health")
def health():
    return {"status": "ok"}