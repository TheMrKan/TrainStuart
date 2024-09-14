from fastapi import FastAPI
from routers import products, baskets, orders, delivery
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(baskets.router)
app.include_router(orders.router)
app.include_router(delivery.router)

#app.mount("/static", StaticFiles(directory="static"), name="static")
