#これはどっちかというとpythonのサーバプログラム
import cv2
import numpy as np
import base64
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse # 追加：ファイルを返すための機能
from deepface import DeepFace
import json
import uvicorn

app = FastAPI()

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
        while True:#一回websocketで接続したら無限ループで常に待ち受ける
            data = await websocket.receive_text()#script.js側で画像データはテキストデータに変換されてる
            
            # JSON形式で送られてくる場合を想定（chat機能追加を見据えて）
            # もし画像URLだけ送るなら今のままでOKですが、エラー回避のためtryで囲みます
            try:
                encoded_data = data.split(',')[1]#送られてきたテキストデータを画像データに戻す
                nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                emotion_en = results[0]['dominant_emotion']
                
                #script.js側に結果を返信
                await websocket.send_text(json.dumps({
                    "status": "success",
                    "emotion": EMOTION_DICT.get(emotion_en, emotion_en)
                }))
            except Exception:
                continue 
    except Exception as e:
        print(f"Disconnected: {e}")

#pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)