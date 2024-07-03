from fastapi import APIRouter

from controllers.scrape import scrape_website, upload_file

scrape_router = APIRouter()

# scrape router
scrape_router.include_router(scrape_website.router)
scrape_router.include_router(upload_file.router)