# from app.db import engine

# print(engine)
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchone())