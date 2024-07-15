from fastapi import APIRouter, HTTPException
from server.routers.models import ProductSummary, ProductDetails
import server.core.products.repository as products_repo
import server.core.products.manager as products_manager


router = APIRouter(prefix="/products")


@router.get("/list")
def get_list() -> list[ProductSummary]:
    products = products_repo.all()

    summaries = []
    for prod in products:
        summary = ProductSummary(
            prod.id,
            prod.name,
            prod.icon_url,
            prod.price,
            products_manager.is_available(prod)
        )
        summaries.append(summary)

    return summaries


@router.get("/{product_id}")
def get_details(product_id: str) -> ProductDetails:
    product = products_repo.by_id(product_id)
    if not product:
        raise HTTPException(404)
    
    details = ProductDetails(
        product.id,
        product.name,
        product.image_url,
        product.description,
        product.price,
        products_manager.is_available(product)
    )
    
    return details

