from server.core.products.models import Product


FAKE_PRODUCTS_DB = {
    "water_still_0,5": Product(
        "water_still_0,5",
        "Минеральная вода 0,5 л",
        "Пол литра минеральной воды без газа в пластиковой бутылке",
        "http://127.0.0.1:8000/static/water_still_0,5_icon.png",
        "http://127.0.0.1:8000/static/water_still_0,5_image.png",
        50,
        5
    ),
    "cola": Product(
        "cola",
        "CocaCola 0,33 л",
        "0,33 литра CocaCola в оригинальной жестяной банке",
        "http://127.0.0.1:8000/static/cola_icon.png",
        "http://127.0.0.1:8000/static/cola_image.png",
        100,
        1
    ),
}


def all() -> list[Product]:
    return list(FAKE_PRODUCTS_DB.values())


def by_id(product_id: str) -> Product | None:
    return FAKE_PRODUCTS_DB.get(product_id, None)