window.addEventListener("channel_ready", function (event) {
  event.detail.channel.addEventListener("code_navigation", function (event) {
    console.log(`Navigation ${event.detail.url}`);
    const first = event.detail.url.indexOf("?");
    let cleaned = event.detail.url;
    if (first !== -1) {
      cleaned = event.detail.url.substring(0, first);
      if (cleaned.endsWith("/")) {
        cleaned = cleaned.substring(0, -1);
      }
    }
    let current = document.location.protocol + "//" + document.location.host + document.location.pathname;
    if (current.endsWith("/")) {
      current = current.substring(0, -1);
    }

    if (current !== cleaned) {
      window.location.href = event.detail.url;
    }
  });
});