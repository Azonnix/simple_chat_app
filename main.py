# from fastapi import (
#     FastAPI, WebSocket, WebSocketDisconnect, Request, Response
# )
# from typing import List
# from pydantic import BaseModel
# from fastapi.templating import Jinja2Templates
#
# app = FastAPI()
#
# # locate templates
# templates = Jinja2Templates(directory="templates")
#
#
# @app.get("/")
# def get_home(request: Request):
#     return templates.TemplateResponse("home.html", {"request": request})
#
#
# @app.get("/chat")
# def get_chat(request: Request):
#     return templates.TemplateResponse("chat.html", {"request": request})
#
#
# @app.get("/api/current_user")
# def get_user(request: Request):
#     return request.cookies.get("X-Authorization")
#
#
# class RegisterValidator(BaseModel):
#     username: str
#
#     class Config:
#         orm_mode = True
#
#
# @app.post("/api/register")
# def register_user(user: RegisterValidator, response: Response):
#     response.set_cookie(key="X-Authorization", value=user.username, httponly=True)
#     return {}
#
#
# class SocketManager:
#     def __init__(self):
#         self.active_connections: List[(WebSocket, str)] = []
#
#     async def connect(self, websocket: WebSocket, user: str):
#         await websocket.accept()
#         self.active_connections.append((websocket, user))
#
#     def disconnect(self, websocket: WebSocket, user: str):
#         self.active_connections.remove((websocket, user))
#
#     async def broadcast(self, data: dict):
#         for connection in self.active_connections:
#             await connection[0].send_json(data)
#
#
# manager = SocketManager()
#
#
# @app.websocket("/api/chat")
# async def chat(websocket: WebSocket):
#     sender = websocket.cookies.get("X-Authorization")
#     if sender:
#         await manager.connect(websocket, sender)
#         response = {
#             "sender": sender,
#             "message": "got connected"
#         }
#         await manager.broadcast(response)
#         try:
#             while True:
#                 data = await websocket.receive_json()
#                 await manager.broadcast(data)
#         except WebSocketDisconnect:
#             manager.disconnect(websocket, sender)
#             response['message'] = "left"
#             await manager.broadcast(response)


from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from typing import List

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

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


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
