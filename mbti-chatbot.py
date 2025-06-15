import streamlit as st
import uuid
from llm import stream_ai_message
import time


# 소개글 리스트
INTRO_LINES = [
    "💬안녕하세요.",
    "MBTI 챗봇에 오신 것을 환영합니다.",
    "궁금했던 나의 성향, 연애 스타일, 업무 스타일, 궁합까지 알려드릴게요!"
]

# 초기 상태
if 'intro_shown' not in st.session_state:
    st.session_state['intro_shown'] = False

# 타이틀
st.markdown("<h1 style='text-align: center; color: pink;'>🎀MBTI 챗봇🎀</h1>", unsafe_allow_html=True)

# 고정 소개글 자리 확보
intro_container = st.empty()

# ✨ 소개글 HTML 생성 함수
def generate_intro_html(lines):
    return '\n'.join(
        f"<p style='text-align: center; font-size: 18px; color: #444;'>{line}</p>"
        for line in lines
    )

# ✅ 애니메이션 + 고정 출력
if not st.session_state['intro_shown']:
    full_html = ""
    for line in INTRO_LINES:
        text = ""
        for char in line:
            text += char
            html = f"<p style='text-align: center; font-size: 18px; color: #444;'>{text}</p>"
            intro_container.markdown(full_html + html, unsafe_allow_html=True)
            time.sleep(0.03)
        full_html += f"<p style='text-align: center; font-size: 18px; color: #444;'>{line}</p>\n"
        time.sleep(0.3)
    intro_container.markdown(full_html, unsafe_allow_html=True)
    st.session_state['intro_shown'] = True
else:
    intro_container.markdown(generate_intro_html(INTRO_LINES), unsafe_allow_html=True)

# 🌐 session_id 관리
query_params = st.query_params
session_id = query_params.get('session_id', str(uuid.uuid4()))
st.query_params.update({'session_id': session_id})
st.session_state.setdefault('session_id', session_id)

# 💬 메시지 리스트 초기화
st.session_state.setdefault('message_list', [])

# 💬 이전 채팅 렌더링
for message in st.session_state.message_list:
    with st.chat_message(message['role']):
        st.write(message['content'])

# 💬 사용자 입력 + 답변
if user_question := st.chat_input("mbti에 대해서 궁금한점을 질문하세요:)"):
    with st.chat_message('user'):
        st.write(user_question)
    st.session_state.message_list.append({'role': 'user', 'content': user_question})

    with st.spinner("답변 생성하는 중입니다. ⏳"):
        ai_message = stream_ai_message(user_question, session_id=st.session_state['session_id'])
        with st.chat_message('ai'):
            ai_message = st.write_stream(ai_message)
        st.session_state.message_list.append({'role': 'ai', 'content': ai_message})