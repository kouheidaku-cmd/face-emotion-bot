# pythonのサーバプログラムでもある
import cv2
import numpy as np
import base64
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse # 追加：ファイルを返すための機能
from deepface import DeepFace
import json
import uvicorn
from openai import OpenAI # OpenAIを利用するためのライブラリに変更
from dotenv import load_dotenv
import os
from pathlib import Path

app = FastAPI()

# ---------------------------- 1. 設定 ----------------------------
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

# OpenAI用の設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
MODEL_NAME = "gpt-4o-mini" # コスパ最強の軽量モデル


# 感情マップ
EMOTION_DICT = {
    "angry": "怒り", "disgust": "嫌悪", "fear": "恐れ",
    "happy": "喜び", "sad": "悲しみ", "surprise": "驚き", "neutral": "自然体"
}

# 画面を出すための設定
@app.get("/")
async def get():
    return FileResponse('static/index.html')

# script.jsをブラウザに送る
@app.get("/script.js")
async def get_js():
    return FileResponse('static/script.js')

# WebSocket 解析ロジック
@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        detected_emotion="不明"

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            if data["type"]=="image":
                try:
                    encoded_data = data["value"].split(',')[1]
                    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emotion_en = results[0]['dominant_emotion']
                    detected_emotion = EMOTION_DICT.get(emotion_en, emotion_en)
                    
                    await websocket.send_text(json.dumps({
                        "status": "emotion_result",
                        "emotion": detected_emotion
                    }))
                except Exception:
                    continue 
            elif data["type"]=="chat":
                user_message=data["value"]
                print(f"Chat message received: {user_message}")
                
                # OpenAI用のプロンプト組み立て
                prompt = (
                            f"あなたは親友です。相手は今「{detected_emotion}」という表情をしています。"
                            f"この感情を考慮して、フランクな日本語で返答してください。\n"
                            f"ユーザー：{user_message}"
                            f"ただし、会話の流れをスムーズにするため返答の生成はできるだけ早く行ってください。"
                            f"また、話し言葉を想定し箇条書きなどは控え、30字以内に抑えてください"
                        )

                # OpenAI APIを呼び出して応答を生成
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "あなたは親切でフランクな親友です。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50 # 30字程度なので制限して節約
                )
                
                ai_response = response.choices[0].message.content
                print(f"OpenAI response: {ai_response}")
                
                # ブラウザに返答を送信
                await websocket.send_text(json.dumps({
                    "status":"chat_response",
                    "value":ai_response
                }))
    except Exception as e:
        print(f"Disconnected: {e}")

# pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)