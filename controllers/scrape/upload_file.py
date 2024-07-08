from bson import ObjectId
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from services.auth import get_current_user_id
import os
import logging
from controllers.data import add_data
from models.auth import User
from controllers.auth.login import get_user_by_user_id

class ScrapeRequest(BaseModel):
    url: str

router = APIRouter()
sped_db = None
user_db = None
sped_vectors_folder = "sped_vectors"
iep_vectors_folder = "iep_vectors"
sped_db = None
user_db = None
sped_vectors_folder = "sped_vectors"
iep_vectors_folder = "iep_vectors"
openai_api_key = os.getenv("OPENAI_API_KEY")

@router.post("/iep_scrape_and_insert")
async def upload_iep_file(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    global user_db
    if not os.path.exists(iep_vectors_folder):
        os.makedirs(iep_vectors_folder)
        
    user_folder = os.path.join(iep_vectors_folder, user_id)
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a PDF")
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        loader = PyPDFLoader(file_location)
        pages = loader.load_and_split()
        
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        if user_db is None:
            user_db = await FAISS.afrom_documents(pages, embeddings)
        else:
            user_db.add_documents(pages)
        
        user_db.save_local(user_folder)
        os.remove(file_location)

        num_documents = len(pages)
        sample_content = [page.page_content[:200] for page in pages[:3]]

        if user_id:
            current_user = await get_user_by_user_id(user_id) #calling the api to get the User object by passing user_id

        if num_documents is not None and sample_content is not None and current_user is not None:
            request_obj = {
                        "name": file.filename,
                        "uploadedUserId":user_id,
                        "uploadedUserRole": current_user.role,
                        "type": 1, #as it is link
                        "status": 3 #as scraping is done
                    }

            inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB

        return JSONResponse(content={
            "detail": "IEP PDF scraped and uploaded successfully.",
            "num_documents": num_documents,
            "sample_content": sample_content,
            "inserted_record": inserted_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))