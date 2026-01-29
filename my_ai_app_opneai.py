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
from fastapi.staticfiles import StaticFiles # これを追加

app = FastAPI()

# ---------------------------- 1. 設定 ----------------------------
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)
# 💡 これを追加！ staticフォルダをブラウザから見えるようにする
app.mount("/static", StaticFiles(directory="static"), name="static")

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
                            f"あなたは感情豊かな１０代の女性です。相手は今「{detected_emotion}」という表情をしています。\n"
                            f"ユーザー：{user_message}\n"
                            "ただし、会話の流れをスムーズにするため返答の生成はできるだけ早く行ってください。\n"
                            "また、話し言葉を想定し箇条書きなどは控え、30字以内に抑えてください\n"
                            "以下のJSON形式で返答してください：\n"
                            "{ \"reply\": \"30字以内の返答\", \"ai_emotion\": \"喜び/悲しみ/驚き/自然体/怒り/嫌悪/恐れ\" }\n" 
                        )

                # OpenAI APIを呼び出して応答を生成
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                response_json=json.loads(response.choices[0].message.content)
                print(f"AI Response: {response_json}")
                # ブラウザに返答を送信
                await websocket.send_text(json.dumps({
                    "status":"chat_response",
                    "reply":response_json["reply"],
                    "ai_emotion":response_json["ai_emotion"]
                }))
    except Exception as e:
        print(f"Disconnected: {e}")

# pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)