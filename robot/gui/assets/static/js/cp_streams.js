
const streams = {};
var activeStream = null;

window.addEventListener("channel_ready", function (event) {

    event.detail.channel.addEventListener("code_stream", function(event) {
        addStream(event.detail.id, event.detail.url, event.detail.name);
    });

});

function addStream(id, url, name) {
    console.log(`Adding stream ${name} (${url})`);
    var imageElement = document.getElementById("stream-image");
    streams[id] = {"id": id, "url": url, "name": name, "stream": new WSVideoStream(url, imageElement)};
    var tabs = document.getElementById("streams-tabs");
    var tabsList = tabs.getElementsByTagName("ul")[0];
    tabsList.insertAdjacentHTML("beforeend", `<li id="stream-button-${id}"><a onclick="onStreamClicked('${id}')">${name}</a></li>`);
}

function onStreamClicked(id) {
    if (activeStream?.id == id) {
        stopActiveStream();
    }
    else {
        setActiveStream(id);
    }
}

function setActiveStream(id) {
    if (activeStream) {
        stopActiveStream();
    }

    var stream = streams[id];
    if (!stream) {
        console.log(`Unknown stream ${id}`);
        return;
    }

    activeStream = stream;
    document.getElementById(`stream-button-${id}`).classList.add("is-active");
    activeStream.stream.begin();
}

function stopActiveStream() {
    if (!activeStream) {
        return;
    }

    activeStream.stream.stop();
    var tabsList = document.getElementById("streams-tabs").getElementsByTagName("ul")[0];
    tabsList.childNodes.forEach((el) => {
        el.classList?.remove("is-active");
    });
    activeStream = null;
}