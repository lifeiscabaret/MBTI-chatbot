import streamlit as st
import uuid
from llm import stream_ai_message

# 페이지 설정
st.set_page_config(page_title="🎀MBTI 챗봇🎀", page_icon="🩷", layout="centered")

# 핑크 타이틀 + 소개
st.markdown("""
    <h1 style='text-align: center; color: pink;'>🎀MBTI 챗봇🎀</h1>
    <p style='text-align: center;'>안녕하세요. MBTI 챗봇에 오신 것을 환영합니다.<br>
    궁금했던 나의 성향, 연애 스타일, 업무 스타일, 궁합까지 알려드릴게요!</p>
""", unsafe_allow_html=True)

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