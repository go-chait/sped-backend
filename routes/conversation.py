from fastapi import APIRouter

from controllers.conversation import chat_query, get_user_conversation

chat_router = APIRouter()

# chat router
chat_router.include_router(chat_query.router)
chat_router.include_router(get_user_conversation.router)
