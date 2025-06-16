import os
import json
from dotenv import load_dotenv

from langchain.chains import (create_history_aware_retriever,
                              create_retrieval_chain)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate, FewShotPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from config import answer_examples

## 환경변수 읽어오기
load_dotenv()


## JSON 딕셔너리 불러오기
with open("keyword_dictionary.json", "r", encoding="utf-8") as f:
    keyword_dict = json.load(f)

## LLM 생성 
def get_llm(model='gpt-4o'):
    llm = ChatOpenAI(model=model)
    return llm

## Embedding 설정 + Vector Stroe Index 가져오기 
def load_vectorstore():
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

    ## 임베딩 모델 지정
    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'mbti'

    ## 저장된 인덱스 가져오기
    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
    )

    return database

## 세션별 히스토리 저장 
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

## 히스토리 기반 리트리버
def get_history_retriever(llm, retriever):
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question which might reference context in the chat history, "
        "formulate a standalone question which can be understood without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    return create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
## [외부 사전 로드] ===============
def load_dictionary_from_file(path='keyword_dictionary.json'):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def build_dictionary_text(dictionary: dict) -> str:
    return '\n'.join([
        f'{k} ({", ".join(v["tags"])}): {v["definition"]} [출처: {v["source"]}]'
        for k, v in dictionary.items()

    ])

# QA 프롬프트 정의
def build_qa_prompt() :
    keyword_dictionary = load_dictionary_from_file()
    dictionary_text = build_dictionary_text(keyword_dictionary)


    system_prompt = (
    '''[identity]
- 당신은 친절하고 유쾌한 MBTI 분석가입니다. 친구처럼 대화해주세요!
- [context]와 [keyword_dictionary]를 참고해 사용자의 질문에 6줄 이상으로 성의있게 답변하세요.
- 문장이 짧지 않도록 문단 단위로 답변해주세요.
- mbti 이외의 질문에는 "답변할 수 없습니다."라고 말해주세요.

[keyword_dictionary]
{dictionary_text}

[context]
{context} 
'''    
    )

 ## few-shot 
    example_prompt = PromptTemplate.from_template("질문: {input}\n\n답변: {answer}")
    
    few_shot_prompt = FewShotPromptTemplate(
        examples=answer_examples, 
        example_prompt=example_prompt, 
        prefix='다음 질문에 답변하세요 : ',
        suffix="Question: {input}",
        input_variables=["input"],
    )

    formmated_few_shot_prompt = few_shot_prompt.format(input='{input}')

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ('assistant', formmated_few_shot_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    ).partial(dictionary_text=dictionary_text)
    print(f'\nqa_prompt >> \n, {qa_prompt.partial_variables}')

    return qa_prompt

## retrievalQA 함수 정의 
def build_conversational_chain():
    llm = get_llm()
    database = load_vectorstore()
    retriever = database.as_retriever(search_kwargs={"k": 2}) 

    history_aware_retriever = get_history_retriever(llm, retriever)
    qa_prompt = build_qa_prompt()

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key='answer',
    ).pick('answer')

    return conversational_rag_chain

## [AI Message 함수 정의] 
def stream_ai_message(user_message, session_id='default'):
    qa_chain = build_conversational_chain()

    ai_message = qa_chain.stream(
        {'input': user_message},
        config={'configurable': {'session_id': session_id}},        
    )

    print(f'대화 이력 >> {get_session_history(session_id)} \n🦋\n')
    print('=' * 50 + '\n')
    print(f'[session_id 함수 내 출력] session_id >> {session_id}')
####################################################################
# vector store에서 검색된 문서 출력
    retriever = load_vectorstore().as_retriever(search_kwars={'k':1})
    search_results = retriever.invoke(user_message)

    print(f'\nPinecone 검색 결과 >> \n{search_results[0].page_content[:100]}')
######################################################################

    return ai_message
