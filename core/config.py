#環境変数や定数管理を行う
import os
from dotenv import load_dotenv
from pathlib import Path

#.envの読み込み
current_dir = Path(__file__).parent.absolute()
PROJECT_ROOT = current_dir.parent#親ディレクトリにアクセス
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini" 

#システムプロンプト
with open(PROJECT_ROOT/"static/character/ai_profile.txt","r",encoding="utf-8") as f:
    AI_SYSTEM_PROMPT=f.read()

