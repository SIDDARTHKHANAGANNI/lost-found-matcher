from sqlalchemy import text
from app.database import engine, Base
from app import models  # noqa: F401

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("DB initialized: pgvector extension + tables created")