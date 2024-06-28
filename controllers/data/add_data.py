from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi_versioning import version
from db.mongodb import Data
from models.data import DataObj
from bson import ObjectId
import datetime
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import tempfile
import fitz

router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
    return text    

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


@router.post("/retrieve/")
async def retrieve(request: str = Form(...), file: UploadFile = File(...)):
    try:
        
        if file.filename.endswith('.pdf'):
            file = extract_text_from_pdf(file)


        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(await file.read())
        temp_file.close()
        
        text_loader = TextLoader(file_path=temp_file.name)
        documents = text_loader.load()

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        data = FAISS.from_documents(docs, embeddings)

        query = request

        docs = data.similarity_search(query)

        retriever = data.as_retriever()
        docs = retriever.invoke(query)
    
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": docs[0].page_content,
                "query":query,
                "file":file.filename
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