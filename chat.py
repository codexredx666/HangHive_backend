import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>HangHive - Chat</title>
        <style>
            :root {
                --primary: #056162;
                --bg: #0b141a;
                --text: #e9edef;
                --surface: #202c33;
                --sent-bg: #005c4b;
                --received-bg: #202c33;
                --system-bg: rgba(32, 44, 51, 0.6);
            }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                background: var(--bg); 
                color: var(--text);
                display: flex;
                flex-direction: column;
                height: 100vh;
                background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
                background-blend-mode: overlay;
            }
            header {
                padding: 0.75rem 1.5rem;
                background: #202c33;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                z-index: 10;
            }
            header h1 {
                font-size: 1.25rem;
                margin: 0;
            }
            #chat-container {
                flex: 1;
                overflow-y: auto;
                padding: 1.5rem 5%;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            .message-wrapper {
                display: flex;
                flex-direction: column;
                width: 100%;
                margin-bottom: 2px;
            }
            .message {
                max-width: 65%;
                padding: 0.5rem 0.75rem;
                border-radius: 8px;
                word-wrap: break-word;
                line-height: 1.4;
                font-size: 0.9rem;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
            }
            .received {
                background: var(--received-bg);
                align-self: flex-start;
                border-top-left-radius: 0;
            }
            .sent {
                background: var(--sent-bg);
                align-self: flex-end;
                border-top-right-radius: 0;
            }
            .system {
                align-self: center;
                font-size: 0.75rem;
                color: #8696a0;
                background: var(--system-bg);
                padding: 0.3rem 0.6rem;
                border-radius: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0.75rem 0;
                box-shadow: none;
            }
            .sender-name {
                font-size: 0.75rem;
                color: #53bdeb;
                font-weight: 600;
                margin-bottom: 0.2rem;
            }
            .sent .sender-name {
                display: none;
            }
            #input-area {
                padding: 0.75rem 1.5rem;
                background: #202c33;
                display: flex;
                gap: 0.75rem;
                align-items: center;
            }
            input {
                flex: 1;
                background: #2a3942;
                border: none;
                padding: 0.6rem 1rem;
                border-radius: 8px;
                color: white;
                outline: none;
                font-size: 0.95rem;
            }
            button {
                background: transparent;
                color: #8696a0;
                border: none;
                padding: 0.5rem;
                cursor: pointer;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: color 0.2s;
            }
            button:hover {
                color: var(--text);
            }
            button svg {
                width: 24px;
                height: 24px;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>HangHive Chat</h1>
            <span id="ws-id" style="font-size: 0.8rem; color: #8696a0;"></span>
        </header>
        <div id="chat-container"></div>
        <form id="input-area" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" placeholder="Type a message"/>
            <button type="submit">
                <svg viewBox="0 0 24 24" height="24" width="24" preserveAspectRatio="xMidYMid meet" fill="currentColor"><path d="M1.101 21.757L23.8 12.028 1.101 2.3l.011 7.912 13.623 1.816-13.623 1.817-.011 7.912z"></path></svg>
            </button>
        </form>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = "My ID: " + client_id;
            var ws = new WebSocket(`ws://${window.location.host}/ws/${client_id}`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const container = document.getElementById('chat-container');
                
                const wrapper = document.createElement('div');
                wrapper.classList.add('message-wrapper');
                
                const message = document.createElement('div');
                message.classList.add('message');
                
                if (data.type === 'system') {
                    message.classList.add('system');
                    message.textContent = data.content;
                } else {
                    if (data.sender == client_id) {
                        message.classList.add('sent');
                        message.textContent = data.content;
                    } else {
                        message.classList.add('received');
                        const sender = document.createElement('div');
                        sender.classList.add('sender-name');
                        sender.textContent = "Client #" + data.sender;
                        message.appendChild(sender);
                        const text = document.createTextNode(data.content);
                        message.appendChild(text);
                    }
                }
                
                wrapper.appendChild(message);
                container.appendChild(wrapper);
                container.scrollTop = container.scrollHeight;
            };

            function sendMessage(event) {
                var input = document.getElementById("messageText")
                if (input.value) {
                    ws.send(input.value)
                    input.value = ''
                }
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.broadcast({"type": "system", "content": f"Client #{client_id} joined"})
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({
                "type": "chat",
                "sender": client_id,
                "content": data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({"type": "system", "content": f"Client #{client_id} left"})


