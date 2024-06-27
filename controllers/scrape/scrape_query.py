from glob import glob
import requests
import os
import getpass
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from langchain.document_loaders import PyPDFLoader,WebBaseLoader
from langchain.vectorstores import FAISS
from langchain import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

router = APIRouter()
os.environ['OPENAI_API_KEY'] = getpass.getpass('OpenAI API Key:')
db = None
vectors_folder = "./vectors" 

def load_vectors():
    global db
    try:
        if os.path.exists(vectors_folder):
            db = FAISS.load_local(vectors_folder)
    except Exception as e:
        print(f"Failed to load vectors: {e}")

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    global db
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a PDF")
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        loader = PyPDFLoader(file_location)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        if db is None:
            db = FAISS.from_documents(docs, embeddings)
        else:
            db.add_documents(docs, embeddings)
        db.save_local("vectors_folder")
        results = []
        retriever = db.as_retriever()
        results = retriever.invoke()
        os.remove(file_location)
        return JSONResponse(content={"detail": "PDF uploaded and processed successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/")
async def scrape_website(url: str):
    global db
    try:
        loader = WebBaseLoader(url)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        if db is None:
            db = FAISS.from_documents(docs, embeddings)
        else:
            db.add_documents(docs, embeddings)
        db.save_local(vectors_folder)
        results = []
        retriever = db.as_retriever()
        results = retriever.invoke()
        return JSONResponse(content={"detail": "Website scraped and processed successfully."})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

