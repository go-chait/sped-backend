from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_versioning import VersionedFastAPI, version
from routes.auth import auth_routers
from routes.sessions import sessions_router
from routes.users import users_router
from routes.data import data_router
from routes.conversation import chat_router
from routes.scrape import scrape_router

app = FastAPI()

app = VersionedFastAPI(app, version_format="{major}", prefix_format="/v{major}")

# List of allowed origins
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
@version(1)
def helth_care():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ok"})


# app.include_router(api_routers)
app.include_router(auth_routers, tags=["Auth"])

app.include_router(users_router, prefix="/users", tags=["User"])

app.include_router(sessions_router, prefix="/session", tags=["Session"])

app.include_router(data_router, prefix="/data", tags=["Data"])

app.include_router(chat_router, prefix="/chat-query", tags=["Chat"])

app.include_router(scrape_router, prefix="/scrape", tags=["Scrape"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
