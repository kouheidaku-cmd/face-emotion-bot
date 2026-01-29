const video = document.getElementById('webcam');//index.htmlのid=webcam要素を取得,ビデオ本体
const canvas = document.getElementById('canvas');//pythonサーバに送信する画像データの一時保管用キャンバス
const emotion = document.getElementById('emotion-display');//htmlの感情表示要素を取得
const chatLog=document.getElementById("chat-log"); //htmlのチャット返信表示要素を取得
const context = canvas.getContext('2d');//キャンバスの2Dコンテキストを取得
const aiFace=document.getElementById("ai-face");
const aiStatus=document.getElementById("ai-status");

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
        li.innerHTML=`<strong>AI:</strong> ${data.reply}`;//リストアイテムの内容を設定

        chatLog.appendChild(li);
        

        //AIの表情を変換
        const aiEmotion=data.ai_emotion;
        if(aiEmotion==="喜び"){
            aiFace.src="static/character/happy.png";
            aiStatus.innerText="AIの状態: 喜び";
        }else if(aiEmotion==="悲しみ"){ 
            aiFace.src="static/character/sad.png";
            aiStatus.innerText="AIの状態: 悲しみ";
        }else if(aiEmotion==="驚き"){
            aiFace.src="static/character/surprised.png";
            aiStatus.innerText="AIの状態: 驚き";
        }else if(aiEmotion==="怒り"){
            aiFace.src="static/character/angry.png";
            aiStatus.innerText="AIの状態: 怒り";
        }else if(aiEmotion==="嫌悪"){               
            aiFace.src="static/character/disgusted.png";
            aiStatus.innerText="AIの状態: 嫌悪";
        }else if(aiEmotion==="恐れ"){               
            aiFace.src="static/character/fearful.png";
            aiStatus.innerText="AIの状態: 恐れ";
        }else{ //自然体などその他
            aiFace.src="static/character/neutral.png";
            aiStatus.innerText="AIの状態: 自然体";
        }
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