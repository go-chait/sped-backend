import os
import getpass
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyPDFLoader,WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_text_splitters import CharacterTextSplitter
from services import scrape_service

router = APIRouter()
os.environ['OPENAI_API_KEY'] = getpass.getpass('OpenAI API Key:')
llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
db = None

def load_vectors():
    global db
    try:
        if os.path.exists(llm["path"]):
            db = FAISS.load_local(llm["path", llm["embeddings"]])
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
        if os.path.exists(llm["path"]) and os.path.isfile(f"{llm['path']}/vectors"): 
            old_db = FAISS.load_local( llm["path"], llm["embeddings"], allow_dangerous_deserialization=True)
            db.merge_from(old_db)
        db.save_local(llm["path"])
        os.remove(file_location)
        result = await scrape_service.summarize()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "result": result},)
    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(error)},
        )

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
        if os.path.exists(llm["path"]) and os.path.isfile(f"{llm['path']}/vectors"): 
            old_db = FAISS.load_local( llm["path"], llm["embeddings"], allow_dangerous_deserialization=True)
            db.merge_from(old_db)
        db.save_local(llm["path"])
        result = await scrape_service.summarize()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "result": result},)
    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(error)},
        )