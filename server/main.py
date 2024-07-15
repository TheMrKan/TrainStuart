from fastapi import FastAPI
from routers import products, baskets, orders, delivery
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.include_router(products.router)
app.include_router(baskets.router)
app.include_router(orders.router)
app.include_router(delivery.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
