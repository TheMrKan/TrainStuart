
const streams = {};
var activeStream = null;

window.addEventListener("channel_ready", function (event) {

    event.detail.channel.addEventListener("code_stream", function(event) {
        if (event.detail.id in streams) {
            updateStream(event.detail.id, event.detail.url, event.detail.name);
        }
        else {
            addStream(event.detail.id, event.detail.url, event.detail.name);
        }
    });

});

function addStream(id, url, name) {
    const imageElement = document.getElementById("stream-image");
    console.log(`Adding stream ${name} (${url})`);

    streams[id] = {"id": id, "url": url, "name": name, "stream": new WSVideoStream(url, imageElement)};
    var tabs = document.getElementById("streams-tabs");
    var tabsList = tabs.getElementsByTagName("ul")[0];
    tabsList.insertAdjacentHTML("beforeend", `<li id="stream-button-${id}"><a onclick="onStreamClicked('${id}')">${name}</a></li>`);
}

function updateStream(id, url, name) {
    const stream = streams[id];
    if (stream === undefined)
    {
        return;
    }

    const imageElement = document.getElementById("stream-image");
    stream.url = url;
    stream.stream.stop();
    stream.stream = new WSVideoStream(url, imageElement);

    stream.name = name;
    const button = document.querySelector(`#stream-button-${id} a`);
    button.innerText = name;
}

function onStreamClicked(id) {
    if (activeStream?.id === id) {
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

    const stream = streams[id];
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