###### AI 케릭터 서버 ######

아키텍처
FastAPI 기반 RESTful API 서버로 구성되어 있으며, 세션 기반 인증과 외부 AI API 연동을 통한 채팅봇 서비스를 제공합니다.

# 미들웨어 설정
세션 관리
    SessionMiddleware - 사용자 세션 데이터를 암호화하여 쿠키에 저장
CORS 설정  
    CORSMiddleware - 웹 브라우저에서의 크로스 도메인 요청 허용

# 사용자 관리 기능
# 회원가입 (POST /user)
사용자명 중복 검사
SHA256으로 비밀번호 해싱
메모리 기반 사용자 데이터 저장

# 로그인/로그아웃
python# 로그인 (POST /user/login)
- 비밀번호 검증 후 세션에 사용자 정보 저장
- session["username"], session["logged_in"], session["login_time"] 설정

# 로그아웃 (POST /user/logout)  
- 전체 세션 데이터 삭제
- require_login 의존성 주입으로 인증 확인

# 인증 시스템
# 의존성 주입 기반 인증
pythondef get_current_user(request: Request) -> Optional[str]:
    # 세션에서 사용자명 추출

def require_login(request: Request) -> str:
    # 로그인 필수 검증, 미인증 시 401 에러

이 패턴을 통해 보호가 필요한 엔드포인트에 current_user: str = Depends(require_login) 추가만으로 인증 적용이 가능합니다.

# 채팅 기능
# 일반 채팅 (POST /chat/conversation)
  대화 맥락 유지를 위한 전체 메시지 히스토리 전송
  시스템 메시지 자동 추가
  사용자별 세션 기반 대화 기록 저장
  외부 API 호출 및 에러 처리

# 역할 기반 채팅 (POST /chat/role)
  미리 정의된 역할별 시스템 프롬프트
  동적 역할 생성 지원
  단발성 대화 (히스토리 미유지)

# 데이터 관리
# 세션 기반 기록 저장
    pythonsession_key = f"conversation_history_{current_user}"
    request.session[session_key].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "user_message": user_input,
        "ai_response": ai_output
    })
# 기록 관리 API
    GET /chat/history - 사용자별 채팅 기록 조회
    DELETE /chat/history - 사용자별 기록 삭제


# 개선 필요 영역
    비밀번호 해싱: bcrypt 등 더 강력한 알고리즘 권장
    세션 만료 시간 설정
    실제 데이터베이스 연동 필요
    API 속도 제한 미구현

# 아키텍처 특징
# 장점:

    의존성 주입으로 깔끔한 인증 처리
    세션 기반으로 상태 유지 가능
    모듈화된 구조로 확장성 좋음

# 제한사항:

    메모리 기반 저장으로 서버 재시작 시 데이터 손실
    단일 서버 환경에서만 세션 공유 가능
    대용량 트래픽 처리에는 추가 최적화 필요

# endpoint
# 서버 상태 확인
GET / - 서버 실행 상태 확인

# 사용자 관리 (User Management)
POST /user - 회원가입
POST /user/login - 로그인 (세션 생성)
POST /user/logout - 로그아웃 (세션 삭제) [로그인 필요]
GET /user/profile - 현재 로그인된 사용자 프로필 조회 [로그인 필요]
GET /users/ - 전체 사용자 목록 조회 [로그인 필요]

# 채팅 기능 (Chat Features)
POST /chat/conversation - 일반 채팅 (대화 맥락 유지) [로그인 필요]
POST /chat/role - 역할 기반 채팅 (시인, 파이썬 선생님 등) [로그인 필요]

# 채팅 기록 관리 (Chat History)
GET /chat/history - 사용자별 채팅 기록 조회 [로그인 필요]
DELETE /chat/history - 사용자별 채팅 기록 삭제 [로그인 필요]

# 엔드포인트 상세 정보:
# 인증 불필요:

GET / - 서버 상태
POST /user - 회원가입
POST /user/login - 로그인

# 인증 필요 (세션 기반):
POST /user/logout - 로그아웃
GET /user/profile - 프로필 조회
GET /users/ - 사용자 목록
POST /chat/conversation - 일반 채팅
POST /chat/role - 역할 채팅
GET /chat/history - 채팅 기록 조회
DELETE /chat/history - 채팅 기록 삭제