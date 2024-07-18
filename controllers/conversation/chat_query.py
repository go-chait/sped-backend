from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi_versioning import version
from fastapi.responses import JSONResponse
from services.chat_service import handle_chat_query
from langchain_core.messages.utils import get_buffer_string
from models.conversations import ChatEntry
from utils.conversations import add_chat_to_conversation
from services.auth import get_current_user_id
from bson import ObjectId  
from db.mongodb import Users


router = APIRouter()


@router.post("/query")
@version(1)
async def chat_query(request: Request, user_id: str = Depends(get_current_user_id)):
    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Query is required"},
            )

        user_obj_id = ObjectId(user_id)
        user = Users.find_one({"_id": user_obj_id}, {"password": 0})

        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "User not found"},
            )

        response = await handle_chat_query(user_id, query)

        chat_entry = ChatEntry(
            question=query,
            AI=response['data']["output"]
        )

        success = add_chat_to_conversation(user_id, chat_entry)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add chat to conversation")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "response": response['data']},
        )
    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(error)},
        )