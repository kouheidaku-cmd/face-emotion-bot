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


chat_history=[]

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
        #通信が始まって一回目の顔写真の送信の際にモデルの初期設定を行う
        raw_data = await websocket.receive_text()
        first_contact(raw_data)

        while True:
            detected_emotion="不明"
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            #-----------------画像データの処理------------------
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
            #-----------------チャットデータの処理------------------
            elif data["type"]=="chat":
                response_json=make_response(data,detected_emotion)
                # ブラウザに返答を送信
                await websocket.send_text(json.dumps({
                    "status":"chat_response",
                    "reply":response_json["reply"],
                    "ai_emotion":response_json["ai_emotion"]
                }))
    except Exception as e:
        print(f"Disconnected: {e}")

#通信が始まった瞬間の通信,一回目の顔写真の受信の際にモデルの初期設定を行う関数
def first_contact(raw_data):
    global chat_history
    data = json.loads(raw_data)
    if data["type"]=="image":
        encoded_data = data["value"].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = DeepFace.analyze(frame, actions=['age','gender','race'], enforce_detection=False)
        user_age = results[0]['age']
        user_gender=results[0]['gender']
        user_race=results[0]['race']
        print(f"User info - Age: {user_age}, Gender: {user_gender}, Race    : {user_race}")

        #プロンプト組み立て
        user_content = (
                    "あなたが今会話をしているユーザーはあなたと仲の良い友人であり、情報は以下の通りです。\n"
                    f"年齢:{user_age}歳、性:{user_gender}、人種:{user_race}\n"
                    )
        f=open('static/character/ai_profile.txt','r',encoding='utf-8')
        ai_content=f.read()
        f.close()

        #chat_historyの履歴に最初の初期設定を追加
        chat_history.append({"role": "system","content":ai_content})
        chat_history.append({"role": "user", "content": user_content})


#チャットデータの返信
def make_response(data,now_emotion):
    global chat_history
    user_message=data["value"]
    #ユーザーのメッセージ保存
    chat_history.append({"role":"user","content":f"表情:{now_emotion} {user_message}"})
    print(f"Chat message received: {user_message}")
    
    # OpenAI用のプロンプト組み立て
    prompt = (
                f"相手は今「{now_emotion}」という表情をしています。\n"
                f"ユーザーからのメッセージ：{user_message}\n"
                "会話の流れをスムーズにするため返答の生成はできるだけ早く行ってください。\n"
                "また、話し言葉を想定し箇条書きなどは控え、30字以内に抑えてください\n"
                "以下のJSON形式で返答してください：\n"
                "{ \"reply\": \"30字以内の返答\", \"ai_emotion\": \"喜び/悲しみ/驚き/自然体/怒り/嫌悪/恐れ\" }\n" 
            )
    
    current_messages = chat_history + [{"role": "user", "content": prompt}]

    # OpenAI APIを呼び出して応答を生成
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=current_messages,#この時履歴も一緒に渡す
        response_format={"type": "json_object"}
    )
    
    response_json=json.loads(response.choices[0].message.content)
    print(f"AI Response: {response_json}")
    #chat_historyの更新
    chat_history.append({"role":"assistant","content":response_json["reply"]})
    # 履歴が長くなりすぎるとエラーになるので、初期設定は残して直近10件くらいに絞るのが一般的
    if len(chat_history) > 11:
        chat_history = [chat_history[0]] +[chat_history[1]] + chat_history[-10:]
    return response_json


# pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)