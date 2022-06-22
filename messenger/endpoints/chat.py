from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from deps import get_db, get_current_user
import crud.chat as crud
import crud.message as crud_message
import crud.user as crud_user
from schemas.chat import Chat, ChatInDB
from schemas.chat_user import ChatUserInDB, ChatUser
from schemas.user import User, UserInDB
from schemas.message import Message

from core.broker.redis import redis

router = APIRouter(prefix="/chat")


@router.get("/", response_model=ChatInDB)
async def get_chat(chat_id, db=Depends(get_db)):
    """Получить чат по заданному chat_id"""
    chat = crud.get_chat_by_id(db=db, chat_id=chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return chat


@router.get("/members", response_model=List[UserInDB])
async def get_chat_members(chat_id: int, db=Depends(get_db)):
    """Получить всех пользователей чата"""
    chat = crud.get_chat_members(db=db, chat_id=chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return chat


@router.get("/my", response_model=List[ChatInDB])
async def get_chat_members(user_id=Depends(get_current_user), db=Depends(get_db)):
    """Получить свои чаты"""
    chat = crud.get_all_chats_of_user(db=db, user_id=user_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return chat


@router.post("/", response_model=ChatInDB)
async def create_chat(chat: Chat, user_id=Depends(get_current_user), db=Depends(get_db)):
    """Создать чат"""
    result = crud.create_chat(db=db, user_id=user_id, chat=chat)
    message = crud_message.create_message(db=db, message=Message(user_id=user_id, chat_id=result.id, text=f"Chat {chat.name} created", edited=False, read=False))
    return result


@router.post("/invite", response_model=ChatUserInDB)
async def invite_friend_to_chat(friend: ChatUser, user_id=Depends(get_current_user), db=Depends(get_db)):
    """Добавить друга в чат"""
    result = crud.add_user_in_chat(db=db, chat_user=friend)
    user = crud_user.get_user_by_id(db=db, user_id=result.user_id)
    message = crud_message.create_message(db=db, message=Message(user_id=user_id, chat_id=result.chat_id, text=f"Your friend {user.name} joined the party!", edited=False, read=False))
    return result