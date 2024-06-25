from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi_versioning import version
from db.mongodb import Data
from models.data import DataObj
from bson import ObjectId
import datetime


router = APIRouter()


@router.post("/addData")
@version(1)
async def add(request: DataObj):
    try:
        if DataObj is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Object should not be null"},
            )
        
        #converting the object into dictionary
        data_dict = request.dict()

        data_dict["createdDate"] = datetime.datetime.utcnow()

        #validations
        if data_dict["name"] is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Name should not be null"},
            )
        
        if data_dict["type"] is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Type should not be null"},
            )
        
        else:
            data_dict["type"] = request.type.name

        if data_dict["status"] is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Status should not be null"},
            )
        
        else:
            data_dict["status"] = request.status.name

        if data_dict["link"] is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Link should not be null"},
            )
            

        inserted_result = Data.insert_one(data_dict)
        data_id = str(inserted_result.inserted_id)
       

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": data_id,
            },
        )
    except Exception as error:
        code = (
            error.status_code
            if hasattr(error, "status_code")
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        message = error.content if hasattr(error, "content") else str(error)

        return JSONResponse(
            status_code=code,
            content={"error": f"{message}"},
        )