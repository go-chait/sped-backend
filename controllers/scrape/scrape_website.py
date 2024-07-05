from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os
import logging

class ScrapeRequest(BaseModel):
    url: str

router = APIRouter()
db = None
vectors_folder = "sped_vectors"
openai_api_key = os.getenv("OPENAI_API_KEY")

@router.post("/link")
async def scrape_website(request: ScrapeRequest):
    global db
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not set")

        url = request.url
        loader = WebBaseLoader(url)
        documents = loader.load()

        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        if db is None:
            db = await FAISS.afrom_documents(docs, embeddings)
        else:
            db.add_documents(docs, embeddings)
            logging.info("Added documents to existing FAISS index")

        db.save_local(vectors_folder)

        results = [doc.page_content for doc in docs[:5]]  

        return JSONResponse(content={"detail": "Website scraped and processed successfully.", "results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
