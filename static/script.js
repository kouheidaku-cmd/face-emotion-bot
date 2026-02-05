const video = document.getElementById('webcam');//index.htmlのid=webcam要素を取得,ビデオ本体
const canvas = document.getElementById('canvas');//pythonサーバに送信する画像データの一時保管用キャンバス
const emotion = document.getElementById('emotion-display');//htmlの感情表示要素を取得
const chatLog=document.getElementById("chat-log"); //htmlのチャット返信表示要素を取得
const context = canvas.getContext('2d');//キャンバスの2Dコンテキストを取得
const aiFace=document.getElementById("ai-face");
const aiStatus=document.getElementById("ai-status");
let currentEmotionImg="/static/character/neutral.png";//グローバル変数でAIの感情画像を保持
let currentEmotionImg2="/static/character/neutral-2.png";
let currentEmotionImg3="/static/character/neutral-3.png";
let mouthInterval=null;//口パクの状態を管理する変数
let speak_frag=0;

// カメラを起動する関数
async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        // --- 💡 ここに音声認識の開始を追加 ---
        // recognition が外側で定義されている前提です
        if (recognition) {
            recognition.start();
            console.log("音声認識を開始しました（ハンズフリーモード）");
        }
        // ------------------------------------

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
        //音声の発生
        speak(data.reply);

        //チャットログに返信を追加
        const li = document.createElement("li");//新しいリストアイテム要素を作成
        li.style.marginBottom="10px";//リストアイテムの下に余白を追加
        li.innerHTML=`<strong>AI:</strong> ${data.reply}`;//リストアイテムの内容を設定
        chatLog.appendChild(li);

        //AIの表情を変換
        const aiEmotion=data.ai_emotion;
        if(aiEmotion==="喜び"){
            currentEmotionImg="static/character/happy.png";
            currentEmotionImg2="static/character/happy-2.png";
            currentEmotionImg3="static/character/happy-3.png";
            aiStatus.innerText="AIの状態: 喜び";
        }else if(aiEmotion==="悲しみ"){ 
            currentEmotionImg="static/character/sad.png";
            currentEmotionImg2="static/character/sad-2.png";
            currentEmotionImg3="static/character/sad-3.png";
            aiStatus.innerText="AIの状態: 悲しみ";
        }else if(aiEmotion==="驚き"){
            currentEmotionImg="static/character/surprised.png";
            currentEmotionImg2="static/character/surprised-2.png";
            currentEmotionImg3="static/character/surprised-3.png";
            aiStatus.innerText="AIの状態: 驚き";
        }else if(aiEmotion==="怒り"){
            currentEmotionImg="static/character/angry.png";
            currentEmotionImg2="static/character/angry-2.png";
            currentEmotionImg3="static/character/angry-3.png";
            aiStatus.innerText="AIの状態: 怒り";
        }else if(aiEmotion==="嫌悪"){               
            currentEmotionImg="static/character/disgusted.png";
            currentEmotionImg2="static/character/disgusted-2.png";
            currentEmotionImg3="static/character/disgusted-3.png";
            aiStatus.innerText="AIの状態: 嫌悪";
        }else if(aiEmotion==="恐れ"){               
            currentEmotionImg="static/character/fearful.png";
            currentEmotionImg2="static/character/fearful-2.png";
            currentEmotionImg3="static/character/fearful-3.png";
            aiStatus.innerText="AIの状態: 恐れ";
        }else{ //自然体
            currentEmotionImg="static/character/neutral.png";
            currentEmotionImg2="static/character/neutral-2.png";
            currentEmotionImg3="static/character/neutral-3.png";
            aiStatus.innerText="AIの状態: 自然体";
        }
        aiFace.src=currentEmotionImg
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

//ボタンを押してチャット送信の関数
function submitaction(){
    const chatInput=document.getElementById("chat-input");
    if (chatInput.value.trim()===""){
        return;
    }
    const data={
        type:"chat",
        value:chatInput.value
    }
    socket.send(JSON.stringify(data));
    chatInput.value = ""; // index側の入力欄を空にする
}



//エンターキーでチャット送信
function enterKeyPress(event){
    if(event.key==="Enter"){
        submitaction();
    }
}

//音声を発声させる関数
function speak(text) {
    if (!window.speechSynthesis) {
        console.error('このブラウザは音声読み上げに対応していません');
        return;
    }

    speak_frag=1;//話してる時のfragを上げる

    //今発生している音を中断、ちなみにwindowはブラウザのタブそのものを表すjsの最上位のオブジェクト
    window.speechSynthesis.cancel();

    const resumeInfinity=setInterval(()=>{
        if (!window.speechSynthesis.speaking){
            clearInterval(resumeInfinity);
        }else{
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
        }
    },10000);

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'ja-JP';
    utter.rate = 1.0;
    utter.pitch = 1.5;

    utter.onstart = () => {//utter.onstartという変数に処理そのものを代入、utterが始まった途端start操作を行う
        console.log("onstart fired");
        if (mouthInterval) clearInterval(mouthInterval);//mouthIntervalが存在する場合削除

        mouthInterval = setInterval(() => {
            aiFace.src = aiFace.src.includes(currentEmotionImg)
                ? currentEmotionImg2
                : currentEmotionImg;
        }, 200);
    };


    // 💡 読み上げ終了
    utter.onend = () => {
        if (mouthInterval) {
            clearInterval(mouthInterval);
            mouthInterval = null;
        }
        // 終了時は確実に「閉じ口」に戻す
        aiFace.src = currentEmotionImg;
        console.log("口パク終了");
        setTimeout(()=>{//プログラムとブラウザのタイムラグを埋める調整
            speak_frag=0;
            console.log("マイク有効");
        },1000);
    };

    window.speechSynthesis.speak(utter);//ここで音声の発話を行う
}

//瞬きを行う関数
function startBlinking(){
    //瞬きを行う感覚をランダムに生成
    const nextBlinking=Math.random()*3000+3000;

    //nextBlinking後に以下の動作を行う
    setTimeout(()=>{
        //AIがしゃべっていないときに瞬きさせる
        if(!mouthInterval){
            aiFace.src=currentEmotionImg3;
            //150ミリ秒後普通の顔に戻す
            setTimeout(()=>{
                aiFace.src=currentEmotionImg;
                startBlinking();
            },200);
        }else{
            startBlinking();
        }
    },nextBlinking);
}


// ページ読み込み時にまばたきを開始
window.onload = () => {
    startBlinking();
};

//---------------------------------音声入力----------------------------------
// 音声認識の準備
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.lang = 'ja-JP';      // 日本語
recognition.interimResults = false; // 確定した結果だけ受け取る
recognition.continuous = true;   // 常に聞き続ける

// 音声を認識した時の処理
recognition.onresult = (event) => {
    if (speak_frag==0){//AIの発話中聞き取り機能オフに
        const transcript = event.results[event.results.length - 1][0].transcript.trim();
        if (transcript) {
            console.log("認識された声:", transcript);
            
            // 入力欄に文字を入れて、そのまま送信関数を呼ぶ
            const chatInput = document.getElementById("chat-input");
            chatInput.value = transcript;
            submitaction(); 
        }
    }
};

// エラーや停止時の自動再起動
recognition.onend = () => {
    recognition.start(); // 止まったら自動で再開（聞き続けさせる）
};

// 0.5秒ごとに画像を送信
startWebcam().then(() => {
    setInterval(sendFrame, 500); 
});

//ボタンを押すことによりチャット送信
const sendButton=document.getElementById("send-button");//htmlの送信ボタン要素を取得
sendButton.addEventListener("click",submitaction);

