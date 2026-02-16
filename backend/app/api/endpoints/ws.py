from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.redis_service import RedisService
import asyncio
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    redis = RedisService.get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("appointments_updates")

    async def reader():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await websocket.send_text(message["data"])
                await asyncio.sleep(0.1) 
        except Exception:
            pass

    task = asyncio.create_task(reader())

    try:
        while True:
            # Keep connection open, ignore incoming messages from client for now
            # In a real chat app we would broadcast them
            await websocket.receive_text()
    except WebSocketDisconnect:
        task.cancel()
        await pubsub.unsubscribe("appointments_updates")
