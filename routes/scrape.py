from fastapi import APIRouter
from controllers.scrape import scrape_data,

scrape_router = APIRouter()

# scrape router
scrape_router.include_router(scrape_data.process_data)