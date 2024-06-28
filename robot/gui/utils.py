from webview import Window


def send_url(window: Window, url: str):
    """
    Открывает указанный HTML файл в окне. Если этот файл уже открыт, то перезагружает его
    """
    if window.get_current_url().endswith(url.split("/")[-1]):
        window.evaluate_js("window.location.reload();")
    else:
        window.load_url(url)