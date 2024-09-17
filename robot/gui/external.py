from robot.config import instance as config
import urllib.parse


def get_product_url(product_id: str) -> str:
    return urllib.parse.urljoin(config.server.web_domain, f"shop.html?product_id={product_id}")