from fastapi import APIRouter

from controllers.scrape import scrape_query

pdfscrape_router = APIRouter()
webscrape_router = APIRouter()
retrievedata_router = APIRouter()
# pdf scrape router
pdfscrape_router.include_router(scrape_query.upload_file.router)

# Web scrape router
webscrape_router.include_router(scrape_query.scrape_website.router)