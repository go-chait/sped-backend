from fastapi import APIRouter, HTTPException, Request, status
from fastapi_versioning import version
from fastapi.responses import JSONResponse
from services.chat_service import handle_chat_query
import faiss
import numpy as np


router = APIRouter()


@router.post("/query")
@version(1)
async def chat_query(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Query is required"},
            )

        response = await handle_chat_query(query)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "response": response},
        )
    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(error)},
        )
    


class VectorSearchTool:
    def __init__(self, dimension, index_type='FlatL2'):
        self.dimension = dimension

        self.index = faiss.index_factory(dimension, index_type)

        def add_vectors(self, vectors):
            # Convert vectors to float32 (required by FAISS)
            vectors = vectors.astype('float32')
        
            # Add vectors to the index
            self.index.add(vectors)

        def search_vectors(self, query_vector, k=5):
        
            # Ensure query_vector is of the correct type and shape
            query_vector = np.array(query_vector).astype('float32').reshape(1, -1)
        
            # Perform search
            distances, indices = self.index.search(query_vector, k)
        
            return distances[0], indices[0]
        

        
