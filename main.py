#----------------プログラム全体を管理するサーバプログラム-----------
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse 
from fastapi.staticfiles import StaticFiles 
from services.chat_service import ChatService
import uvicorn#こいつがサーバ


#fastapiインスタンスはいろんなファイルをつなぐルーティングを行う、ちなみにサーバではない
app = FastAPI()
#フロントエンド部分をユーザ側に公開、これをしないと画像とかにアクセスできなくなる
app.mount("/static", StaticFiles(directory="static"), name="static")

#インスタンス化
chat_service=ChatService()

#------以下ルーティング------
@app.get("/")
async def get():
    return FileResponse('static/index.html')

@app.get("/chatscript.js")
async def get_js():
    return FileResponse('static/chatscript.js')

# WebSocket 応答ロジック
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print("Client connected")
    try:
        while True:
            # クライアント(ユーザ側)からテキスト（JSON形式）を受信
            data = await websocket.receive_json()
            if data["type"] == "chat":
                # AIから返答を取得
                response = chat_service.get_response(data["value"])
                print(response)
                # クライアントへ返信
                await websocket.send_json({
                    "status": "chat_response",
                    "reply": response["reply"],
                    "ai_emotion": response["ai_emotion"]
                })
    except Exception as e:
        print(f"Connection closed: {e}")



# pythonサーバの立ち上げ
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)