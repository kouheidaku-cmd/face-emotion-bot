const video = document.getElementById('webcam');//index.htmlのid=webcam要素を取得,ビデオ本体
const canvas = document.getElementById('canvas');//pythonサーバに送信する画像データの一時保管用キャンバス
const emotion = document.getElementById('emotion-display');//htmlの感情表示要素を取得
const chatLog=document.getElementById("chat-log"); //htmlのチャット返信表示要素を取得
const context = canvas.getContext('2d');//キャンバスの2Dコンテキストを取得

//カメラを起動する関数
async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;//カメラで撮影される映像streamをvideoのsrcObjectに設定
    } catch (err) {
        console.error("カメラの起動に失敗しました: ", err);
    }
}

//WebSocketの接続設定 (Python側のURLに合わせる)
//ウェブブラウザとサーバー間で永続的かつ双方向の通信を可能にする通信プロトコル
const socket = new WebSocket('ws://localhost:8000/ws/analyze');

socket.onmessage = (event) => {//サーバーからメッセージ(判定された感情)を受信したときの処理
    const data = JSON.parse(event.data);
    if (data.status === "emotion_result") {//サーバーからメッセージ(判定された感情)を受信したときの処理
        emotion.innerText = "あなたの感情： " + data.emotion;//emotion要素のテキストを更新
    }
    if (data.status==="chat_response"){//サーバーからgeminiの返答を受信したときの処理
        const li = document.createElement("li");//新しいリストアイテム要素を作成
        li.style.marginBottom="10px";//リストアイテムの下に余白を追加
        li.innerHTML=`<strong>AI:</strong> ${data.value}`;//リストアイテムの内容を設定
        //alert(data.value);
        chatLog.appendChild(li);

        // 自動で一番下までスクロールさせる
        const container = document.getElementById('chat-container');
        container.scrollTop = container.scrollHeight;
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
        const data={
            type:"image",
            value:imageData
        };
        socket.send(JSON.stringify(data));//dataをjson形式{ "type": "chat", "value": "こんにちは" }に変換
    }
}

//ボタンを押してチャット送信
function buttonClick(){
    const chatInput=document.getElementById("chat_input");
    const data={
        type:"chat",
        value:chatInput.value
    }
    socket.send(JSON.stringify(data));
    chatInput.value = ""; // index側の入力欄を空にする
}

// 0.5秒ごとに画像を送信
startWebcam().then(() => {
    setInterval(sendFrame, 500); 
});
const sendButton=document.getElementById("send_button");//htmlの送信ボタン要素を取得
sendButton.addEventListener("click",buttonClick);