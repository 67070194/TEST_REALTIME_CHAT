from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()

rooms = {}

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
    
    async def broadcast(self, message: str, sender: WebSocket):
        for connection in self.active_connections:
            if connection != sender:  
                await connection.send_text(message)

@app.get("/rooms")
async def get_rooms():
    return list(rooms.keys())

@app.get("/")
async def get():
    return FileResponse('templates/index.html')

@app.get("/chat/{room_name}")
async def get_chat(room_name: str):
    return FileResponse('templates/chat.html')

@app.websocket("/ws/{room_name}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, username: str):
    if room_name not in rooms:
        rooms[room_name] = ConnectionManager()

    manager = rooms[room_name]
    await manager.connect(websocket)
    await manager.broadcast(f"{username} joined the chat", websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} left the chat", websocket)
