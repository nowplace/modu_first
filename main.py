from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import User, ChatResponse, ConversationRequest, Message
import datetime
import hashlib
import httpx
from typing import List, Dict

app = FastAPI(title="부트캠프 ChatGPT API 서버", version="0.0.1")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용자 데이터 저장소 (실제 프로젝트에서는 데이터베이스 사용)
users = []

# 부트캠프 API 엔드포인트 URL
BOOTCAMP_API_URL = "https://dev.wenivops.co.kr/services/openai-api"


# 로그인 요청 모델
class LoginRequest(BaseModel):
    username: str
    password: str


# GET 요청: 서버 상태 확인
@app.get("/")
async def root():
    return {"message": "부트캠프 ChatGPT API 서버가 실행 중입니다"}


@app.post("/user")
async def create_user(data: User):
    # 중복 사용자 확인
    for user in users:
        if user["username"] == data.username:
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

    user = {
        "username": data.username,
        "password": hashlib.sha256(data.password.encode("utf-8")).hexdigest(),
        "created_at": datetime.datetime.now(),
    }
    users.append(user)
    return {"message": "사용자가 성공적으로 생성되었습니다", "username": data.username}


@app.post("/user/login")
async def login_user(data: LoginRequest):
    for user in users:
        if user["username"] == data.username:
            if (
                user["password"]
                == hashlib.sha256(data.password.encode("utf-8")).hexdigest()
            ):
                return {"message": "로그인 성공", "username": data.username}
    raise HTTPException(
        status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다"
    )


@app.get("/users/")
async def get_users():
    # 비밀번호는 제외하고 반환
    return [
        {"username": user["username"], "created_at": user["created_at"]}
        for user in users
    ]


@app.post("/chat/conversation", response_model=ChatResponse)
async def conversation_chat(request: ConversationRequest):
    """
    대화 맥락을 유지하는 채팅 함수
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


@app.post("/chat/role")
async def role_based_chat(role: str, message: str):
    """
    특정 역할을 가진 AI와 채팅
    """
    # 역할에 따른 system 메시지 생성
    role_prompts = {
        "시인": "assistant는 시인이다. 모든 답변을 아름다운 시의 형태로 표현한다.",
        "파이썬 선생님": "assistant는 친절한 파이썬 알고리즘의 힌트를 주는 선생님이다.",
        "요리사": "assistant는 경험이 풍부한 요리사다. 맛있는 요리법을 알려준다.",
        "여행 가이드": "assistant는 세계 여행 전문가로서, 각 도시의 관광지, 음식, 교통 팁을 제공한다.",
    }

    system_message = role_prompts.get(role, f"assistant는 {role}이다.")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
