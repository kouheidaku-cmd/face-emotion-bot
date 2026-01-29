import google.generativeai as genai

# あなたのAPIキーに書き換えてください
genai.configure(api_key="AIzaSyChKRqmEi2qf_NQjFFJEzkpybpgY25xsPg")

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