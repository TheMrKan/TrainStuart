window.addEventListener("load",() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("auth")) {
        const current = document.location.protocol + "//" + document.location.host + document.location.pathname;
        const url = `http://server:8002/static/login.html?next=${current}&ticket=${params.get("auth")}`;
        window.location.href = url;
    }
})