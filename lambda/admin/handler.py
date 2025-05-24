import os
import databases, sqlalchemy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/taptupoadmin"
)
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
apis = sqlalchemy.Table(
    "apis", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, unique=True),
    sqlalchemy.Column("url", sqlalchemy.String),
    sqlalchemy.Column("method", sqlalchemy.String),
    sqlalchemy.Column("headers", sqlalchemy.JSON, nullable=True),
)
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

class APIIn(BaseModel):
    name: str
    url: str
    method: str
    headers: dict = {}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/admin/apis")
async def create_api(api: APIIn):
    query = apis.insert().values(**api.dict())
    api_id = await database.execute(query)
    return { "id": api_id, **api.dict() }

@app.get("/admin/apis")
async def list_apis():
    return await database.fetch_all(apis.select())

@app.delete("/admin/apis/{api_id}")
async def delete_api(api_id: int):
    await database.execute(apis.delete().where(apis.c.id == api_id))
    return { "deleted": api_id }

handler = Mangum(app)
