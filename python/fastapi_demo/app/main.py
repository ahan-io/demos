from fastapi import FastAPI
import asyncio
from pydantic import BaseModel


# 定义请求模型
class PingRequest(BaseModel):
    name: str = "world"

# 定义响应模型
class PingResponse(BaseModel):
    message: str


app = FastAPI()


@app.post("/ping", response_model=PingResponse)
async def ping(req: PingRequest):
    # 模拟异步操作（比如 I/O）
    await asyncio.sleep(0.1)
    return PingResponse(message=f"pong, {req.name}")
