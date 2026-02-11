from openai import OpenAI
from core.config import OPENAI_API_KEY,MODEL_NAME,AI_SYSTEM_PROMPT
import json

#AIチャットに関するクラスを定義、この基本的な機能はすべてのユーザに共通
class ChatService:
    def __init__(self):
        self.client=OpenAI(api_key=OPENAI_API_KEY)
        self.chat_history=[{"role":"system","content":AI_SYSTEM_PROMPT}]
    
    def get_response(self,user_text):
        #ユーザ履歴を追加
        self.chat_history.append({"role":"user","content":user_text})
        print(user_text)
        # OpenAI用のプロンプト組み立て
        prompt = (
                    f"ユーザーからのメッセージ：{user_text}\n"
                    "会話の流れをスムーズにするため返答の生成はできるだけ早く行ってください。\n"
                    "また、話し言葉を想定し箇条書きなどは控えてください\n"
                    "以下のJSON形式で返答してください：\n"
                    "{ \"reply\": \"返答\", \"ai_emotion\": \"喜び/悲しみ/驚き/自然体/怒り/嫌悪/恐れ\" }\n" 
                    "注意点としてai_emotionには心配は含まれておりません"
                )
        current_messages = self.chat_history + [{"role": "user", "content": prompt}]

        # OpenAI APIを呼び出して応答を生成
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=current_messages,#この時履歴も一緒に渡す
            response_format={"type": "json_object"}
        )
        response_json=json.loads(response.choices[0].message.content)
        #chat_historyの更新
        self.chat_history.append({"role":"assistant","content":response_json["reply"]})

        # 履歴が長くなりすぎるとエラーになるので、初期設定は残して直近10件くらいに絞るのが一般的
        if len(self.chat_history) > 11:
            self.chat_history = [self.chat_history[0]] + self.chat_history[-10:]

        return response_json