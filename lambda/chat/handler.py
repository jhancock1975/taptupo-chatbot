import os, requests
from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
from qdrant_client import QdrantClient
from model_control_protocol import Client as MCPClient
import databases, sqlalchemy

app = FastAPI()

# Qdrant client
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    port=int(os.getenv("QDRANT_PORT"))
)

# MCP client
mcp = MCPClient({
    "openai": {"api_key": os.getenv("OPENAI_API_KEY")},
    "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")}
})

# Database setup
DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/taptupoadmin"
)
database = databases.Database(DB_URL)
metadata = sqlalchemy.MetaData()
apis_table = sqlalchemy.Table("apis", metadata, autoload_with=sqlalchemy.create_engine(DB_URL))

class ChatReq(BaseModel):
    message: str
    namespace: str = "default"

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/chat")
async def chat(req: ChatReq):
    hits = qdrant.search(
        collection_name=req.namespace,
        query_vector=qdrant.embed(req.message),
        limit=3
    )
    context = "\n".join(hit.payload["text"] for hit in hits)
    prompt = f"You are an assistant. Docs:\n{context}\nUser: {req.message}\nAssistant:"
    tools = await database.fetch_all(apis_table.select())
    stream = mcp.generate(
        model="gpt-4",
        prompt=prompt,
        stream=True,
        tool_registry=tools
    )
    return stream

handler = Mangum(app)
