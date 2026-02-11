//html要素の取得
const chatLog=document.getElementById("chat-log"); //チャットの履歴の表示欄
const chatInput=document.getElementById("chat-input");//chatの入力欄
const sendButton=document.getElementById("send-button");//chatの送信ボタン要素を取得
const aiFace=document.getElementById("ai-face");//aiの顔
const aiStatus=document.getElementById("ai-status");//aiの感情

//AIの表情画像のパス管理
let currentEmotionImg="/static/character/neutral.png";//グローバル変数でAIの感情画像を保持
let currentEmotionImg2="/static/character/neutral-2.png";
let currentEmotionImg3="/static/character/neutral-3.png";

let mouthInterval=null;//口パクの状態を管理する変数
let speak_frag=0;//発話のフラッグ

// 音声認識を起動する関数
async function start_listen() {
    try {
        if (recognition) {
            recognition.start();
            console.log("音声認識を開始しました（ハンズフリーモード）");
        }
        // ------------------------------------

    } catch (err) {
        console.error("カメラの起動に失敗しました: ", err);
    }
}


//1,WebSocketの接続設定 (Python側のURLに合わせる)
//ウェブブラウザとサーバー間で永続的かつ双方向の通信を可能にする通信プロトコル
const socket = new WebSocket('ws://localhost:8000/ws/chat');


socket.onmessage = (event) => {//サーバーからメッセージ(判定された感情)を受信したときの処理
    const data = JSON.parse(event.data);

    if (data.status==="chat_response"){//サーバーからAIの返答を受信したときの処理
        //音声の発生
        speak(data.reply);

        //チャットログに返信を追加
        const li = document.createElement("li");//新しいリストアイテム要素を作成
        li.style.marginBottom="10px";//リストアイテムの下に余白を追加
        li.innerHTML=`<strong>AI:</strong> ${data.reply}`;//リストアイテムの内容を設定
        chatLog.appendChild(li);

        //AIの表情を変換
        updateAiFace(data.ai_emotion);
        
    }
};

//2,AIの感情を切り替える関数
function updateAiFace(ai_emotion){
    const emotions={
        "喜び": "happy",
        "悲しみ": "sad",
        "驚き": "surprised",
        "怒り": "angry",
        "嫌悪": "disgusted",
        "恐れ": "fearful",
        "自然体":"neutral"
    };
    currentEmotionImg = `/static/character/${emotions[ai_emotion]}.png`;
    currentEmotionImg2 = `/static/character/${emotions[ai_emotion]}-2.png`;
    currentEmotionImg3 = `/static/character/${emotions[ai_emotion]}-3.png`;

    aiFace.src=currentEmotionImg
    aiStatus.innerText=`AIの状態:${ai_emotion}`
}


//3,メッセージ送信関数
function submitaction(){
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

//4,音声を発声させる関数
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

//5,瞬きを行う関数
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

//6,音声入力を行う関数
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


//ボタンを押すことによりチャット送信
sendButton.addEventListener("click",submitaction);

start_listen()

