from robot.config import instance as config
import urllib.parse


SHOP = "shop.html"
TAXI = "https://taxi.yandex.ru/"
HOTELS = "https://ostrovok.ru"


def get_product_url(product_id: str) -> str:
    return get_server_url(f"{SHOP}?product_id={product_id}")


def get_server_url(sub_path: str = ""):
    return urllib.parse.urljoin(config.server.web_domain, sub_path)
