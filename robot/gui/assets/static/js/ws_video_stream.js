class WSVideoStream {
    constructor(socketUrl, imageElement) {
        this.socketUrl = socketUrl;
        this.imageElement = imageElement;
        this.socket = null;
    }

    begin() {
        if (this.socket) {
            return;
        }

        this.socket = new WebSocket(this.socketUrl);

        this.socket.onopen = () => {
            console.log("WebSocket соединение открыто.");
        };

        this.socket.onmessage = (event) => {
            const blob = new Blob([event.data], { type: 'image/png' });

            const imageUrl = URL.createObjectURL(blob);

            this.imageElement.src = imageUrl;

            this.imageElement.onload = () => {
                URL.revokeObjectURL(imageUrl);
            };
        };

        this.socket.onclose = (event) => {
            console.log("WebSocket соединение закрыто.");
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket ошибка:", error);
        };
    }

    stop() {
        if (this.socket) {
            this.socket.close();
            console.log("WebSocket соединение остановлено.");
            this.socket = null;
        }
    }
}