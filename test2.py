import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 1. パスの絶対指定
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"

# 2. 読み込みの実行と結果確認
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True) # overrideを追加して強制上書き
    print(f"DEBUG: .envファイルを見つけました: {env_path}")
else:
    print(f"DEBUG: .envファイルが {current_dir} に見つかりません！")

# 3. キーの取得
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    print(f"✅ APIキーを取得しました (先頭4文字: {API_KEY[:4]}...)")
    # ここで設定を完結させる
    genai.configure(api_key=API_KEY)
else:
    print("❌ エラー: 環境変数 'GEMINI_API_KEY' が空です。.envの中身を確認してください。")

# --- この後に FastAPI の app 定義などを続ける ---