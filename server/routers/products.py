from fastapi import APIRouter, HTTPException
from typing import List

from server.routers.models import ProductSummary, ProductDetails
import server.core.products as products


router = APIRouter(prefix="/products")


@router.get("/list")
def get_list() -> List[ProductSummary]:
    prods = products.all()

    summaries = []
    for prod in prods:
        summary = ProductSummary(
            prod.id,
            prod.name,
            prod.icon_url,
            prod.price,
            products.is_available(prod)
        )
        summaries.append(summary)

    return summaries


@router.get("/{product_id}")
def get_details(product_id: str) -> ProductDetails:
    product = products.by_id(product_id)
    if not product:
        raise HTTPException(404)
    
    details = ProductDetails(
        product.id,
        product.name,
        product.icon_url,
        product.image_url,
        product.description,
        product.price,
        products.is_available(product)
    )
    
    return details

