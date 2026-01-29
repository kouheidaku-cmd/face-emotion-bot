#pythonのサーバプログラムでもある
import cv2
import numpy as np
import base64
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse # 追加：ファイルを返すための機能
from deepface import DeepFace
import json
import uvicorn
import google.generativeai as genai#geminiを利用するためのライブラリ
from dotenv import load_dotenv
import os
from pathlib import Path

app = FastAPI()


# ---------------------------- 1. 設定 ----------------------------
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')


# 感情マップ
EMOTION_DICT = {
    "angry": "怒り", "disgust": "嫌悪", "fear": "恐れ",
    "happy": "喜び", "sad": "悲しみ", "surprise": "驚き", "neutral": "自然体"
}

#画面を出すための設定、立ち上げられたサーバ(127.0.0.1:8000)にアクセスしたときにまずこの操作
@app.get("/")
async def get():#asyncは非同期処理の意味
    # index.htmlをブラウザに送る
    return FileResponse('static/index.html')

#index.htmlファイルをブラウザが受け取りその結果script.jsが必要になるのでそれも送る
@app.get("/script.js")
async def get_js():
    # script.jsをブラウザに送る
    return FileResponse('static/script.js')

#WebSocket 解析ロジック、アプリの心臓部、script.jsを読み込むとさらにここの部分が要求される
@app.websocket("/ws/analyze")# WebSocketという双方向通信の仕組みを使う
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        detected_emotion="不明"

        while True:#一回websocketで接続したら無限ループで常に待ち受ける
            raw_data = await websocket.receive_text()#script.js側で画像データはテキストデータに変換されてる
            data=json.loads(raw_data)#JSON形式のテキストデータを辞書型に変換
            if data["type"]=="image":
                # JSON形式で送られてくる場合を想定（chat機能追加を見据えて）
                try:
                    #print("Image received for emotion analysis")
                    encoded_data = data["value"].split(',')[1]#送られてきたテキストデータを画像データに戻す
                    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emotion_en = results[0]['dominant_emotion']
                    detected_emotion = EMOTION_DICT.get(emotion_en, emotion_en)
                    #script.js側に結果を返信
                    await websocket.send_text(json.dumps({
                        "status": "emotion_result",
                        "emotion": EMOTION_DICT.get(emotion_en, emotion_en)
                    }))
                except Exception:
                    continue 
            elif data["type"]=="chat":
                user_message=data["value"]
                print(f"Chat message received: {user_message}")
                prompt = (
                            f"あなたは親友です。相手は今「{detected_emotion}」という表情をしています。"
                            f"この感情を考慮して、フランクな日本語で返答してください。\n"
                            f"ユーザー：{user_message}"
                            f"ただし、会話の流れをスムーズにするため返答の生成はできるだけ早く行ってください。"
                            f"また、話し言葉を想定し箇条書きなどは控え、30字以内に抑えてください"
                        )
                # ここでGemini APIを呼び出して応答を生成（擬似コード）
                response= model.generate_content(prompt)
                #ブラウザにgeminiの返答を送信
                await websocket.send_text(json.dumps({
                    "status":"chat_response",
                    "value":response.text
                }))
    except Exception as e:
        print(f"Disconnected: {e}")

#pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)