from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os
import logging
from controllers.data import add_data
from services.auth import get_current_user_id
from fastapi.middleware.cors import CORSMiddleware
from controllers.auth.login import get_user_by_user_id

class ScrapeRequest(BaseModel):
    url: str


router = APIRouter()
db = None
sped_db = None
sped_vectors_folder = "sped_vectors"
openai_api_key = os.getenv("OPENAI_API_KEY")

# API that accepts either a json object or a PDF file and inserts into data collection
@router.post("/sped_scrape_and_insert")
async def scrape(request: Request, file: UploadFile = File(default= None), user_id: str = Depends(get_current_user_id)):
    #<editor-fold desc="PDF">
    #If the user uploaded PDF file
    if file is not None:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File is not a PDF")
        try:
            global sped_db
            file_location = f"temp_{file.filename}"
            with open(file_location, "wb") as f:
                f.write(await file.read())
            
            loader = PyPDFLoader(file_location)
            pages = loader.load_and_split()
            
            embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
            if sped_db is None:
                sped_db = await FAISS.afrom_documents(pages, embeddings)
            else:
                sped_db.add_documents(pages)
            
            sped_db.save_local(sped_vectors_folder)
            os.remove(file_location)

            num_documents = len(pages)
            sample_content = [page.page_content[:200] for page in pages[:3]]

            if user_id:
                current_user = await get_user_by_user_id(user_id) #calling the api to get the User object by passing user_id
                print("curent", current_user)

            if num_documents is not None and sample_content is not None and current_user is not None:
                request_obj = {
                        "name": file.filename,
                        "uploadedUserId": user_id,
                        "uploadedUserRole": current_user.role,
                        "type": 2, #as it is PDF
                        "status": 3 #as scraping is done
                    }

                inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB
                
            return JSONResponse(content={
                "detail": "SPED PDF uploaded and processed successfully.",
                "num_documents": num_documents,
                "sample_content": sample_content,
                "inserted_record_id": inserted_id
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    #</editor-fold>

    #<editor-fold desc="Link">
    #If the user uploaded link
    else:
        if request is not None:
            body = await request.body()
            # Parsing request body as JSON
            parsed_json = ScrapeRequest.parse_raw(body)
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise HTTPException(status_code=500, detail="OpenAI API key not set")

                url = parsed_json.url
                if user_id is not None:
                    uploadedUserId = user_id
                    
                loader = WebBaseLoader(url)
                documents = loader.load()

                text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
                docs = text_splitter.split_documents(documents)

                embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
                if sped_db is None:
                    sped_db = await FAISS.afrom_documents(docs, embeddings)
                else:
                    sped_db.add_documents(docs)
                    logging.info("Added documents to existing FAISS index")

                sped_db.save_local(sped_vectors_folder)

                results = [doc.page_content for doc in docs[:5]]  

                if user_id:
                    current_user = await get_user_by_user_id(user_id) #calling the api to get the User object by passing user_id

                if results is not None:
                    request_obj = {
                        "name": url,
                        "uploadedUserId":uploadedUserId,
                        "uploadedUserRole":current_user.role,
                        "type": 1, #as it is link
                        "status": 3 #as scraping is done
                    }

                    inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB
                    
                return JSONResponse(content={
                    "detail": " SPED website scraped and uploaded successfully.", 
                    "results": results,
                    "inserted_record_id": inserted_id
                    })

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    #</editor-fold>