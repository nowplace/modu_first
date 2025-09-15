from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict


class User(BaseModel):
    username: str
    password: str
    created_at: Optional[datetime] = None


# 로그인 요청 모델
class LoginRequest(BaseModel):
    username: str
    password: str


# 단일 메시지의 구조를 정의
class Message(BaseModel):
    role: str  # "system", "user", "assistant" 중 하나
    content: str  # 메시지 내용


# 간단한 채팅 요청 모델
class SimpleChatRequest(BaseModel):
    message: str  # 사용자 메시지
    system_message: str = "You are a helpful assistant."  # AI 역할 설정 (기본값)


# 전체 대화 요청 모델 (대화 맥락 유지용)
class ConversationRequest(BaseModel):
    messages: List[Message]  # 메시지 목록


# 응답 모델
class ChatResponse(BaseModel):
    response: str  # AI의 응답
    usage: Dict  # 토큰 사용량 정보


# 로그인 요청 모델
class LoginRequest(BaseModel):
    username: str
    password: str
