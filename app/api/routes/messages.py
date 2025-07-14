from typing import Union

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from datetime import datetime, timezone

from app.services.chat_services import chatTest


router = APIRouter(prefix="/messages")


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            data_obj = json.loads(data)
            data_obj["id"] = data_obj["id"] + "1";
            data_obj["timestamp"] = datetime.now(timezone.utc).isoformat()
            data_obj["isBot"] = "true";
            print(data_obj)
            await websocket.send_json(data_obj)
    except WebSocketDisconnect:
        print("Cliente desconectado del WebSocket.")
    except Exception as e:
        print(f"Error inesperado en WebSocket: {e}")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data_obj = json.loads(data)
            data_obj["id"] = data_obj["id"] + "1";
            data_obj["timestamp"] = datetime.now(timezone.utc).isoformat()
            data_obj["isBot"] = "true";
            print(f"{data_obj}")

            chatbotResponse=chatTest(msg=data_obj["text"])
            contentAi = chatbotResponse.content
            splits = contentAi.split('</think>', 1)
            cleanResponse = splits[1]
            
            data_obj["text"]= cleanResponse

            await manager.send_personal_message(json.dumps(data_obj), websocket)
            # await manager.broadcast(json.dumps(data_obj))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

