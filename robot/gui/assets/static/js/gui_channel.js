CHANNEL_PATH = "/app"

class GUIChannel extends EventTarget {
    constructor(path) {
        super()
        this.path = path
        this.ready = false;
    }

    connect() {
        this.socket = new WebSocket("ws://robot:8001" + this.path);
        var path = this.path;
        var _channel = this;
        this.socket.onopen = function() {
            console.log(`Connected to channel ${path}`);
            if (!this.ready) {
              window.dispatchEvent(new CustomEvent("channel_ready", {detail: {channel: _channel}}));
            }
            this.ready = true;
        };

        this.socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            _channel.dispatchEvent(new CustomEvent("code_" + data.code, {detail: data}))
        };

        this.socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        this.socket.onclose = function(event) {
            if (event.wasClean) {
                console.log('WebSocket connection closed. Code:', event.code, 'Reason:', event.reason);
            } else {
                console.log('WebSocket connection aborted. Retrying in 1 second...');
                setTimeout(() => _channel.connect(), 1000);
            }
        };
    }
}



window.addEventListener('load', function() {
    console.log(`Waiting connection to the GUI channel '${CHANNEL_PATH}'...`);
    channel = new GUIChannel(CHANNEL_PATH);
    channel.connect();
});