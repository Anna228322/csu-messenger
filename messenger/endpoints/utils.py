"""Различные методы проверки функционала"""
from datetime import datetime
from os import getenv
import pytz

from fastapi import APIRouter, WebSocket, Body, Depends

from deps import get_db, get_current_user

from fastapi.responses import HTMLResponse

from core.broker.celery import celery_app
from core.broker.redis import redis
from utils import async_query

import crud.message as crud_messages

router = APIRouter(prefix="/utils")


@router.post("/send_celery_task")
def send_celery_task(begin_datetime: datetime):
    """Запускает выполнение задачи queue.test
    
    Args:
        begin_datetime: datetime, когда запустить задачу
    """
    timezone = pytz.timezone(getenv("TZ"))
    dt_with_timezone = timezone.localize(begin_datetime)

    celery_app.send_task("queue.test", eta=dt_with_timezone)


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/utils/ws/1");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                event.preventDefault()
                var input = document.getElementById("messageText")
                const json_request_body = JSON.stringify({
                    user_id: 1,
                    chat_id: 1,
                    text: input.value,
                    edited: false,
                    read: false
                });
                console.log(json_request_body);
                fetch(`/message/`, {method: 'POST', headers: { "Content-Type": "application/json" }, body: json_request_body})
                input.value = ''
            }
        </script>
    </body>
</html>
"""


@router.get("/ws-page")
async def ws_page():
    """html-страница с подключением к вебсокету"""
    return HTMLResponse(html)



@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, db=Depends(get_db)):
    if chat_id is None:
        return

    all_messages = crud_messages.get_all_messages_in_chat(db=db, chat_id=chat_id)

    await websocket.accept()

    for message in all_messages:
        await websocket.send_text(message.toJSON())

    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat-{chat_id}")

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)

        if message:
            jsonobj = message["data"].decode()
            await websocket.send_text(jsonobj)


@router.get("/ws-pubsub")
async def ws_pubsub(user_id: int, text: str = "test text"):
    """Публикует событие в очередь пользователя"""
    await redis.publish(f"user-{user_id}", text)


@router.post("/post_process_message")
async def post_process_message(message: str = Body(..., embed=True)):
    """Пост-обработка сообщений: выделение ссылок, упоминаний и и.д."""
    url = "http://lanhost:8085/extra"
    extra = await async_query(task_url=url, text=message)

    return extra
