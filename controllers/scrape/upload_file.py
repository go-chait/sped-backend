from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
import logging

class ScrapeRequest(BaseModel):
    url: str

router = APIRouter()
db = None
vectors_folder = "faiss_vectors"
openai_api_key = os.getenv("OPENAI_API_KEY")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global db
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a PDF")
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        loader = PyPDFLoader(file_location)
        pages = loader.load_and_split()
        
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        if db is None:
            db = await FAISS.afrom_documents(pages, embeddings)
        else:
            db.add_documents(pages, embeddings)
        
        db.save_local(vectors_folder)
        os.remove(file_location)

        num_documents = len(pages)
        sample_content = [page.page_content[:200] for page in pages[:3]]
        return JSONResponse(content={
            "detail": "PDF uploaded and processed successfully.",
            "num_documents": num_documents,
            "sample_content": sample_content
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))