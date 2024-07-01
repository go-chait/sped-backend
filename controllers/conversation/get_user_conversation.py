from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from fastapi_versioning import version
from db.mongodb import Conversation
from core.security.security import require_auth
from bson import ObjectId
from bson import json_util
import json


router = APIRouter()


@router.get("/{userId}/conversation")
@version(1)
def get_user_conversation(userId: str, auth: dict = Depends(require_auth)):
    try:
        conversations = Conversation.find_one({"user_id": userId})

        if conversations is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"No conversations found for user {userId}."},
            )

        conversations["_id"] = str(conversations["_id"])

        serialized_conversations = json.loads(json_util.dumps(conversations))

        return JSONResponse(status_code=status.HTTP_200_OK, content=serialized_conversations)

    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"{str(error)}"},
        )