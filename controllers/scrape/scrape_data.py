from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os
import logging

router = APIRouter()
db = None
vectors_folder = "faiss_vectors"
openai_api_key = os.getenv("OPENAI_API_KEY")

class ScrapeRequest(BaseModel):
    url: str = None

@router.post("/process")
async def process_data(file: UploadFile = File(None), url: str = Form(None)):
    global db
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not set")
        
        if file:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="File is not a PDF")
            
            file_location = f"temp_{file.filename}"
            with open(file_location, "wb") as f:
                f.write(await file.read())
            
            loader = PyPDFLoader(file_location)
            pages = loader.load_and_split()
            os.remove(file_location)
            
            content = pages
            num_documents = len(pages)
            sample_content = [page.page_content[:200] for page in pages[:3]]
        elif url:
            loader = WebBaseLoader(url)
            documents = loader.load()
            
            text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
            content = text_splitter.split_documents(documents)
            
            num_documents = len(content)
            sample_content = [doc.page_content[:200] for doc in content[:3]]
        else:
            raise HTTPException(status_code=400, detail="No file or URL provided")

        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        if db is None:
            db = await FAISS.afrom_documents(content, embeddings)
        else:
            db.add_documents(content, embeddings)
            logging.info("Added documents to existing FAISS index")

        db.save_local(vectors_folder)

        return JSONResponse(content={
            "detail": "Data processed successfully.",
            "num_documents": num_documents,
            "sample_content": sample_content
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
