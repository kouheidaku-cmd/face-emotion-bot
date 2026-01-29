import google.generativeai as genai
from dotenv import load_dotenv
import os

# あなたのAPIキーに書き換えてください
load_dotenv() # .envファイルを読み込む
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

try:
    # モデル名をフルパス形式で試す
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content("こんにちは、テストです。")
    print(f"成功！応答: {response.text}")
except Exception as e:
    print(f"エラー発生: {e}")

    # 失敗した場合は、今使えるモデルを無理やりリストアップする
    print("\n--- 利用可能なモデル一覧 ---")
    try:
        for m in genai.list_models():
            print(m.name)
    except Exception as e2:
        print(f"リスト取得失敗: {e2}")