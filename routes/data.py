from controllers.data import (
    add_data
)
from fastapi import APIRouter

data_router = APIRouter()

data_router.include_router(add_data.router)
