from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os
import logging
from controllers.data import add_data

class ScrapeRequest(BaseModel):
    url: str



router = APIRouter()
db = None
vectors_folder = "faiss_vectors"
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

        if results is not None:
            request_obj = {
                "name": results[0],
                "type": 1, #as it is link
                "link": results[0],
                "status": 3 #as scraping is done
            }

            inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB
            
        return JSONResponse(content={"detail": "Record inserted successfully.", "id": inserted_id})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# API that accepts either a json object or a PDF file and inserts into data collection
@router.post("/scrape_and_insert")

async def scrape(request: Request, file: UploadFile = File(default= None)):
    #<editor-fold desc="PDF">
    #If the user uploaded PDF file
    if file is not None:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File is not a PDF")
        try:
            global db
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
            
            if num_documents is not None and sample_content is not None:
                request_obj = {
                    "name": file.filename,
                    "type": 2, #as it is PDF
                    "status": 3 #as scraping is done
                }

                inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB
                
            # return JSONResponse(content={"detail": "PDF uploaded and processed successfully.", "id": inserted_id})

            return JSONResponse(content={
                "detail": "PDF uploaded and processed successfully.",
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

                if results is not None:
                    request_obj = {
                        "name": url,
                        "type": 1, #as it is link
                        "status": 3 #as scraping is done
                    }

                    inserted_id = await add_data.add_sped_data(request_obj) #calling the api to insert the record in the DB
                    
                return JSONResponse(content={
                    "detail": "Website scraped and processed successfully.", 
                    "results": results,
                    "inserted_record_id": inserted_id
                    })

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    #</editor-fold>