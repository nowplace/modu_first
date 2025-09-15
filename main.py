from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import User, ChatResponse, ConversationRequest, Message, LoginRequest

from typing import List, Dict, Optional
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import datetime
import hashlib
import httpx

app = FastAPI(title="부트캠프 ChatGPT API 서버", version="0.0.1")
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
templates = Jinja2Templates(directory="templates")

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


# 세션에서 현재 사용자 정보 가져오기 (의존성 주입)
def get_current_user(request: Request) -> Optional[str]:
    """세션에서 현재 로그인된 사용자 정보를 가져옵니다"""
    return request.session.get("username")


# 로그인 필수 체크 함수
def require_login(request: Request) -> str:
    """로그인이 필요한 엔드포인트에서 사용하는 의존성"""
    username = get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return username


@app.post("/user/login")
async def login_user(data: LoginRequest, request: Request):
    """사용자 로그인 및 세션 생성"""
    for user in users:
        if user["username"] == data.username:
            if (
                user["password"]
                == hashlib.sha256(data.password.encode("utf-8")).hexdigest()
            ):
                # 세션에 사용자 정보 저장
                request.session["username"] = data.username
                request.session["logged_in"] = True
                request.session["login_time"] = datetime.datetime.now().isoformat()

                return {
                    "message": "로그인 성공",
                    "username": data.username,
                    "session_id": request.session.get("_id", "generated"),
                }

    raise HTTPException(
        status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다"
    )


@app.post("/user/logout")
async def logout_user(request: Request, current_user: str = Depends(require_login)):
    """사용자 로그아웃 및 세션 삭제"""
    request.session.clear()
    return {"message": f"{current_user}님이 로그아웃되었습니다"}


@app.get("/user/profile")
async def get_user_profile(
    request: Request, current_user: str = Depends(require_login)
):
    """현재 로그인된 사용자의 프로필 정보"""
    login_time = request.session.get("login_time")
    return {"username": current_user, "login_time": login_time, "session_active": True}


@app.get("/users/")
async def get_users(current_user: str = Depends(require_login)):
    """사용자 목록 조회 (로그인 필요)"""
    # 비밀번호는 제외하고 반환
    return [
        {"username": user["username"], "created_at": user["created_at"]}
        for user in users
    ]


@app.get("/users/")
async def get_users():
    # 비밀번호는 제외하고 반환
    return [
        {"username": user["username"], "created_at": user["created_at"]}
        for user in users
    ]


@app.post("/chat/conversation", response_model=ChatResponse)
async def conversation_chat(
    request_data: ConversationRequest,
    request: Request,
    current_user: str = Depends(require_login),
):
    """
    대화 맥락을 유지하는 채팅 함수 (로그인 필요)
    """
    # 세션에서 사용자별 대화 기록 관리 (선택사항)
    session_key = f"conversation_history_{current_user}"

    # 메시지 배열을 딕셔너리 형태로 변환
    messages = [
        {"role": msg.role, "content": msg.content} for msg in request_data.messages
    ]

    # system 메시지가 없으면 기본값 추가
    if not any(msg["role"] == "system" for msg in messages):
        messages.insert(
            0,
            {
                "role": "system",
                "content": f"You are a helpful assistant for {current_user}.",
            },
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BOOTCAMP_API_URL, json=messages, timeout=30.0)

            response.raise_for_status()
            response_data = response.json()

            ai_message = response_data["choices"][0]["message"]["content"]
            usage_info = response_data["usage"]

            # 선택사항: 세션에 대화 기록 저장
            if session_key not in request.session:
                request.session[session_key] = []

            request.session[session_key].append(
                {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "user_message": (
                        request_data.messages[-1].content
                        if request_data.messages
                        else ""
                    ),
                    "ai_response": ai_message,
                }
            )

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
async def role_based_chat(
    role: str, message: str, current_user: str = Depends(require_login)
):
    """
    특정 역할을 가진 AI와 채팅 (로그인 필요)
    """
    # 역할에 따른 system 메시지 생성
    role_prompts = {
        "시인": "assistant는 시인이다. 모든 답변을 아름다운 시의 형태로 표현한다.",
        "파이썬 선생님": "assistant는 친절한 파이썬 알고리즘의 힌트를 주는 선생님이다.",
        "요리사": "assistant는 경험이 풍부한 요리사다. 맛있는 요리법을 알려준다.",
        "여행 가이드": "assistant는 세계 여행 전문가로서, 각 도시의 관광지, 음식, 교통 팁을 제공한다.",
    }

    system_message = role_prompts.get(
        role, f"assistant는 {role}이다. 사용자 {current_user}에게 도움을 제공한다."
    )

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
                "user": current_user,
                "user_message": message,
                "ai_response": response_data["choices"][0]["message"]["content"],
                "usage": response_data["usage"],
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history")
async def get_chat_history(
    request: Request, current_user: str = Depends(require_login)
):
    """사용자의 채팅 기록 조회"""
    session_key = f"conversation_history_{current_user}"
    history = request.session.get(session_key, [])
    return {
        "user": current_user,
        "total_conversations": len(history),
        "history": history[-10:],  # 최근 10개만 반환
    }


@app.delete("/chat/history")
async def clear_chat_history(
    request: Request, current_user: str = Depends(require_login)
):
    """사용자의 채팅 기록 삭제"""
    session_key = f"conversation_history_{current_user}"
    if session_key in request.session:
        del request.session[session_key]
    return {"message": f"{current_user}의 채팅 기록이 삭제되었습니다"}


if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)
