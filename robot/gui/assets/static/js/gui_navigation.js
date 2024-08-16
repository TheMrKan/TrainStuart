window.addEventListener("channel_ready", function (event) {
  event.detail.channel.addEventListener("code_navigation", function (event) {
    console.log(`Navigation ${event.detail.url}`)
    if (window.location.href !== event.detail.url) {
      window.location.href = event.detail.url;
    }
  });
});