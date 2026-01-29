const video = document.getElementById('webcam');//index.htmlのid=webcam要素を取得
const canvas = document.getElementById('canvas');
const display = document.getElementById('emotion-display');
const context = canvas.getContext('2d');//キャンバスの2Dコンテキストを取得

//カメラを起動する関数
async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        console.error("カメラの起動に失敗しました: ", err);
    }
}

//WebSocketの接続設定 (Python側のURLに合わせる)
//ウェブブラウザとサーバー間で永続的かつ双方向の通信を可能にする通信プロトコル
const socket = new WebSocket('ws://localhost:8000/ws/analyze');

socket.onmessage = (event) => {//サーバーからメッセージ(判定された感情)を受信したときの処理
    const data = JSON.parse(event.data);
    if (data.status === "success") {
        display.innerText = "あなたの感情： " + data.emotion;
    }
};

// 3. 一定間隔で画像をキャプチャしてサーバーに送る
function sendFrame() {
    if (socket.readyState === WebSocket.OPEN) {
        // ビデオのサイズにキャンバスを合わせる
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // 現在の映像をキャンバスに描画
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // 画像をBase64文字列に変換して送信
        const imageData = canvas.toDataURL('image/jpeg', 0.5); // 0.5は画質（軽量化）
        socket.send(imageData);
    }
}

// 0.5秒ごとに画像を送信
startWebcam().then(() => {
    setInterval(sendFrame, 500); 
});