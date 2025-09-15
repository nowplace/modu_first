# 필요한 라이브러리들을 가져옵니다
from fastapi import FastAPI, HTTPException  # FastAPI 프레임워크와 예외처리
from pydantic import BaseModel  # 데이터 검증을 위한 모델 생성
import httpx  # HTTP 요청을 보내기 위한 라이브러리
from typing import List, Dict  # 타입 힌트를 위한 라이브러리
from models import Message, ConversationRequest, ChatResponse  # 데이터 모델들


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="부트캠프 ChatGPT API 서버", version="1.0.0")

# 부트캠프 API 엔드포인트 URL
BOOTCAMP_API_URL = "https://dev.wenivops.co.kr/services/openai-api"


# 대화 맥락을 유지하는 채팅 엔드포인트
@app.post("/chat/conversation", response_model=ChatResponse)
async def conversation_chat(request: ConversationRequest):
    """
    대화 맥락을 유지하는 채팅 함수
    이전 대화 내역을 모두 포함해서 전송
    """

    # 메시지 배열을 딕셔너리 형태로 변환
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # system 메시지가 없으면 기본값 추가
    if not any(msg["role"] == "system" for msg in messages):
        messages.insert(
            0, {"role": "system", "content": "You are a helpful assistant."}
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BOOTCAMP_API_URL, json=messages, timeout=30.0)

            response.raise_for_status()
            response_data = response.json()

            ai_message = response_data["choices"][0]["message"]["content"]
            usage_info = response_data["usage"]

            return ChatResponse(response=ai_message, usage=usage_info)

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, detail="API 요청 시간이 초과되었습니다"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=f"API 오류: {e}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


# 역할 기반 채팅 (시인, 선생님 등)
@app.post("/chat/role")
async def role_based_chat(role: str, message: str):
    """
    특정 역할을 가진 AI와 채팅

    예시:
    - role: "시인", message: "지구는 왜 파란가요?"
    - role: "파이썬 선생님", message: "반복문을 설명해주세요"
    """

    # 역할에 따른 system 메시지 생성
    if role == "시인":
        system_message = (
            "assistant는 시인이다. 모든 답변을 아름다운 시의 형태로 표현한다."
        )
    elif role == "파이썬 선생님":
        system_message = "assistant는 친절한 파이썬 알고리즘의 힌트를 주는 선생님이다."
    elif role == "요리사":
        system_message = "assistant는 경험이 풍부한 요리사다. 맛있는 요리법을 알려준다."
    else:
        system_message = f"assistant는 {role}이다."

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BOOTCAMP_API_URL, json=messages, timeout=30.0)

            response.raise_for_status()
            response_data = response.json()

            return {
                "role": role,
                "user_message": message,
                "ai_response": response_data["choices"][0]["message"]["content"],
                "usage": response_data["usage"],
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# 서버 실행 코드
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
