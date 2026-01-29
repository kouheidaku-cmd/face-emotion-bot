import streamlit as st
import google.generativeai as genai
from deepface import DeepFace
from PIL import Image
import numpy as np
import cv2

# ---------------------------- 1. 設定 ----------------------------
genai.configure(api_key="AIzaSyChKRqmEi2qf_NQjFFJEzkpybpgY25xsPg")
model = genai.GenerativeModel('models/gemini-2.5-flash')

st.title("表情分析AIチャットボット (DeepFace版)")

# 会話履歴の保持
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------- 2. UI / カメラ入力 ----------------------------
img_file = st.camera_input("今のあなたの表情を撮ってください")

# ---------------------------- 3. DeepFace解析 ----------------------------
detected_emotion = "不明"

if img_file is not None:
    # Streamlitの画像をOpenCV形式に変換
    img = Image.open(img_file)
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # OpenCVはBGR

    with st.spinner('感情を解析中...'):
        try:
            # 感情分析を実行
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotion_en = results[0]['dominant_emotion']
            
            # 日本語に変換
            em_dict = {
                "angry": "怒り", "disgust": "嫌悪", "fear": "恐れ",
                "happy": "喜び", "sad": "悲しみ", "surprise": "驚き", "neutral": "自然体"
            }
            detected_emotion = em_dict.get(emotion_en, emotion_en)
            st.success(f"あなたの今の感情：{detected_emotion}")
        except Exception as e:
            st.error(f"解析エラー: {e}")

# ---------------------------- 4. チャット処理 ----------------------------
# 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("話しかけてみて！"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        # Geminiには「感情のテキスト」だけを送る
        prompt = (
            f"あなたは親友です。相手は今「{detected_emotion}」という表情をしています。"
            f"この感情を考慮して、フランクな日本語で返答してください。\n"
            f"ユーザー：{user_input}"
        )
        
        response = model.generate_content(prompt)
        st.write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})