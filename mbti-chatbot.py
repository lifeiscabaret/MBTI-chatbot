import streamlit as st
import uuid
from llm import stream_ai_message
import time


# 초기 상태
if 'intro_shown' not in st.session_state:
    st.session_state['intro_shown'] = False

# 타이틀
st.markdown("<h1 style='text-align: center; color: pink;'>🎀MBTI 챗봇🎀</h1>", unsafe_allow_html=True)

# 소개글 리스트
lines = [
    "💬안녕하세요.",
    "MBTI 챗봇에 오신 것을 환영합니다.",
    "궁금했던 나의 성향, 연애 스타일, 업무 스타일, 궁합까지 알려드릴게요!"
]

# 🎯 고정 소개글 자리 확보
intro_container = st.empty()

# ✅ 처음 한 번만 애니메이션 + 이후에는 고정 텍스트로 덮어쓰기
if not st.session_state['intro_shown']:
    full_html = ""
    for line in lines:
        text = ""
        for char in line:
            text += char
            html = f"<p style='text-align: center; font-size: 18px; color: #444;'>{text}</p>"
            intro_container.markdown(full_html + html, unsafe_allow_html=True)
            time.sleep(0.03)
        full_html += f"<p style='text-align: center; font-size: 18px; color: #444;'>{line}</p>\n"
        time.sleep(0.3)

    # 애니메이션 후 고정 출력
    intro_container.markdown(full_html, unsafe_allow_html=True)
    st.session_state['intro_shown'] = True
else:
    # 이미 본 경우, 고정 출력
    full_html = ""
    for line in lines:
        full_html += f"<p style='text-align: center; font-size: 18px; color: #444;'>{line}</p>\n"
    intro_container.markdown(full_html, unsafe_allow_html=True)
## URL의 parameter에 session_id 저장 ===============================================
query_params = st.query_params

if 'session_id' in query_params:
    session_id = query_params['session_id']
else:
    session_id = str(uuid.uuid4())
    st.query_params.update({'session_id': session_id}) 
## Streamlit 내부 세션: session id 저장
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = session_id

## Streamlit 내부 세션: 메시지 리스트 초기화
if 'message_list' not in st.session_state:
    st.session_state.message_list = []

print('after) st.session_state >>' , st.session_state)

## 이전 채팅 내용 화면 출력
for message in st.session_state.message_list:
    with st.chat_message(message['role']):
        st.write(message['content'])


## 사용자 질문 -> AI 답변 ======================================================================
placeholder = 'mbti에 대해서 궁금한점을 질문하세요:)'

if user_question := st.chat_input(placeholder=placeholder): ## prompt 창
    ## 사용자 메시지 ##############################
    with st.chat_message('user'):
        ## 사용자 메시지 화면 출력
        st.write(user_question)
    st.session_state.message_list.append({'role': 'user', 'content': user_question})

    ## AI 메시지 ##################################
    with st.spinner('답변 생성하는 중입니다. ⏳'):
        session_id = st.session_state.session_id
        ai_message = stream_ai_message(user_question, session_id=session_id)

        with st.chat_message('ai'):
            ## AI 메시지 화면 출력
            ai_message = st.write_stream(ai_message)
        st.session_state.message_list.append({'role': 'ai', 'content': ai_message})