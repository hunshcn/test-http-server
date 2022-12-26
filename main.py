import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, StreamingResponse, HTMLResponse
from typing import List

app = FastAPI()


@app.get("/", response_class=PlainTextResponse)
async def index():
    return "Hello world"


@app.get("/sleep/block/{t}")
async def sleep_block(t: int):
    await asyncio.sleep(t)
    return f"Hello world after {t}s"


@app.get("/sleep/{t}")
async def sleep(t: int):
    async def g():
        for i in range(t):
            await asyncio.sleep(1)
            if (i + 1) % 2 == 0:
                yield str(i + 1) + "\n"
        yield f"Hello world after {t}s"

    return StreamingResponse(g())


@app.get("/file/{size}m")
async def file_download(size: int):
    async def g():
        for _ in range(size):
            for _ in range(1024):
                yield "a" * 1024

    return StreamingResponse(g(), headers={
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{size}m"',
        'Content-Length': str(size * 1024 * 1024),
    })


# websocket
websocket_html = """
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
            var ws = new WebSocket(location.origin.replace('http', 'ws') + `/ws/${client_id}`);
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


@app.get("/ws")
async def get():
    return HTMLResponse(websocket_html)


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
