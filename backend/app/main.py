from fastapi import FastAPI
from app.routers import items
from app.routers import items, auth
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles



app = FastAPI(title="Lost & Found Matcher API")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(items.router, prefix="/items", tags=["items"])


@app.get("/health")
def health():
    return {"status": "ok"}