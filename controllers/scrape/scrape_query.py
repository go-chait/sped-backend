import requests
import os
import getpass
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from langchain.document_loaders import PyPDFLoader  
from langchain.document_loaders import WebBaseLoader
from services import vector_store
from controllers.data import add_data
from models.data import DataObj

router = APIRouter()
os.environ['OPENAI_API_KEY'] = getpass.getpass('OpenAI API Key:')
@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File is not a PDF")
    try:
        pdf_document = PyPDFLoader.open(stream=await file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        vector_store.add_to_index(text)
        return JSONResponse(content={"text": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/")
#async def scrape_website(url: str):
async def scrape_website(request:DataObj):
    try:
        data_dict = request.dict()
        #response = requests.get(url)
        response = requests.get(data_dict["link"])
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve the URL")
        
        url = WebBaseLoader(response.content, "html.parser")
        text = url.load(separator=' ', strip=True)
        vector_store.add_to_index(text)

        if(text is not None):
            call_add_api = add_data.add(DataObj)

        return JSONResponse(content={"text": text, "id": call_add_api})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))