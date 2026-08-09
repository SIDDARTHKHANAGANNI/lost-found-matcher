from fastapi import FastAPI
from app.routers import items
from app.routers import items, auth


app = FastAPI(title="Lost & Found Matcher API")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(items.router, prefix="/items", tags=["items"])

@app.get("/health")
def health():
    return {"status": "ok"}