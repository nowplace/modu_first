import requests
import json
import sys
from typing import List, Dict


class ChatClient:
    def __init__(self, server_url="http://127.0.0.1:8000"):
        self.server_url = server_url
        self.session = requests.Session()  # 세션 쿠키 자동 관리
        self.current_user = None
        self.conversation_history = []

    def register_user(self):
        """사용자 회원가입"""
        print("\n=== 회원가입 ===")
        username = input("사용자명을 입력하세요: ").strip()
        password = input("비밀번호를 입력하세요: ").strip()

        if not username or not password:
            print("사용자명과 비밀번호를 모두 입력해주세요.")
            return False

        try:
            response = self.session.post(
                f"{self.server_url}/user",
                json={"username": username, "password": password},
            )

            if response.status_code == 200:
                print(f"✅ 회원가입 성공! 환영합니다, {username}님!")
                return True
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 회원가입 실패: {error_detail}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def login_user(self):
        """사용자 로그인 (세션 생성)"""
        print("\n=== 로그인 ===")
        username = input("사용자명을 입력하세요: ").strip()
        password = input("비밀번호를 입력하세요: ").strip()

        if not username or not password:
            print("사용자명과 비밀번호를 모두 입력해주세요.")
            return False

        try:
            response = self.session.post(
                f"{self.server_url}/user/login",
                json={"username": username, "password": password},
            )

            if response.status_code == 200:
                result = response.json()
                self.current_user = username
                print(f"✅ 로그인 성공! 환영합니다, {username}님!")
                print(f"🔐 세션 ID: {result.get('session_id', 'N/A')}")
                return True
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 로그인 실패: {error_detail}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def logout_user(self):
        """사용자 로그아웃 (세션 삭제)"""
        try:
            response = self.session.post(f"{self.server_url}/user/logout")

            if response.status_code == 200:
                result = response.json()
                print(f"👋 {result['message']}")
                self.current_user = None
                self.conversation_history = []
                return True
            else:
                print("❌ 로그아웃 처리 중 오류가 발생했습니다.")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def get_user_profile(self):
        """사용자 프로필 정보 조회"""
        try:
            response = self.session.get(f"{self.server_url}/user/profile")

            if response.status_code == 200:
                result = response.json()
                print(f"\n👤 사용자 프로필:")
                print(f"   - 사용자명: {result['username']}")
                print(f"   - 로그인 시간: {result.get('login_time', 'Unknown')}")
                print(
                    f"   - 세션 상태: {'활성' if result.get('session_active') else '비활성'}"
                )
                return result
            elif response.status_code == 401:
                print("❌ 로그인이 필요합니다.")
                return None
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 프로필 조회 실패: {error_detail}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return None

    def get_all_users(self):
        """모든 사용자 목록 조회 (로그인 필요)"""
        try:
            response = self.session.get(f"{self.server_url}/users/")

            if response.status_code == 200:
                users = response.json()
                print(f"\n👥 등록된 사용자 목록 (총 {len(users)}명):")
                print("-" * 40)
                for i, user in enumerate(users, 1):
                    created_at = user["created_at"]
                    if isinstance(created_at, str):
                        created_at = created_at[:19]  # datetime 형식 단축
                    print(f"{i}. {user['username']} (가입일: {created_at})")
                return users
            elif response.status_code == 401:
                print("❌ 로그인이 필요합니다.")
                return None
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 사용자 목록 조회 실패: {error_detail}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return None

    def get_chat_history(self):
        """서버에서 채팅 기록 조회"""
        try:
            response = self.session.get(f"{self.server_url}/chat/history")

            if response.status_code == 200:
                result = response.json()
                print(result)
                print(
                    f"\n📚 {result['user']}님의 채팅 기록 (총 {result['total_conversations']}개)"
                )
                print("-" * 50)

                if not result["history"]:
                    print("채팅 기록이 없습니다.")
                else:
                    for i, chat in enumerate(
                        result["history"][-5:], 1
                    ):  # 최근 5개만 표시
                        timestamp = (
                            chat["timestamp"][:19] if chat["timestamp"] else "Unknown"
                        )
                        print(f"{i}. [{timestamp}]")
                        print(
                            f"   User: {chat['user_message'][:50]}{'...' if len(chat['user_message']) > 50 else ''}"
                        )
                        print(
                            f"   AI: {chat['ai_response'][:50]}{'...' if len(chat['ai_response']) > 50 else ''}"
                        )
                        print()

                return result
            elif response.status_code == 401:
                print("❌ 로그인이 필요합니다.")
                return None
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 기록 조회 실패: {error_detail}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return None

    def clear_chat_history(self):
        """서버의 채팅 기록 삭제"""
        confirm = (
            input("정말로 서버의 채팅 기록을 삭제하시겠습니까? (y/N): ").strip().lower()
        )
        if confirm != "y":
            print("취소되었습니다.")
            return False

        try:
            response = self.session.delete(f"{self.server_url}/chat/history")

            if response.status_code == 200:
                result = response.json()
                print(f"🗑️ {result['message']}")
                return True
            elif response.status_code == 401:
                print("❌ 로그인이 필요합니다.")
                return False
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 기록 삭제 실패: {error_detail}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def send_message(self, user_message):
        """메시지 전송 및 AI 응답 받기 (세션 기반)"""
        # 대화 기록에 사용자 메시지 추가
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = self.session.post(
                f"{self.server_url}/chat/conversation",
                json={"messages": self.conversation_history},
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result["response"]

                # 대화 기록에 AI 응답 추가
                self.conversation_history.append(
                    {"role": "assistant", "content": ai_response}
                )

                return ai_response
            elif response.status_code == 401:
                print("❌ 세션이 만료되었습니다. 다시 로그인해주세요.")
                self.current_user = None
                return None
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                return f"❌ 오류: {error_detail}"

        except requests.exceptions.RequestException as e:
            return f"❌ 서버 연결 오류: {e}"

    def role_chat(self, role, message):
        """역할 기반 채팅 (세션 기반)"""
        try:
            response = self.session.post(
                f"{self.server_url}/chat/role",
                params={"role": role, "message": message},
            )

            if response.status_code == 200:
                result = response.json()
                return result["ai_response"]
            elif response.status_code == 401:
                return "❌ 세션이 만료되었습니다. 다시 로그인해주세요."
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                return f"❌ 오류: {error_detail}"

        except requests.exceptions.RequestException as e:
            return f"❌ 서버 연결 오류: {e}"

    def test_all_endpoints(self):
        """모든 엔드포인트 테스트"""
        print("\n🧪 === API 엔드포인트 전체 테스트 ===")

        if not self.current_user:
            print("❌ 로그인이 필요합니다.")
            return

        print("\n1. 사용자 프로필 조회 테스트...")
        self.get_user_profile()

        print("\n2. 사용자 목록 조회 테스트...")
        self.get_all_users()

        print("\n3. 일반 채팅 테스트...")
        response = self.send_message("안녕하세요! 테스트 메시지입니다.")
        print(f"AI 응답: {response}")

        print("\n4. 역할 기반 채팅 테스트...")
        response = self.role_chat("시인", "봄에 대해 시를 써주세요")
        print(f"시인 응답: {response}")

        print("\n5. 채팅 기록 조회 테스트...")
        self.get_chat_history()

        print("\n✅ 모든 테스트 완료!")

    def show_help(self):
        """도움말 표시"""
        print("\n📖 === 명령어 도움말 ===")
        print("기본 채팅:")
        print("  - 그냥 메시지 입력: 일반 AI 채팅")
        print("  - /role 역할명 메시지: 역할 기반 채팅")
        print("    예: /role 시인 봄에 대해 써줘")
        print()
        print("사용자 관리:")
        print("  - /profile: 내 프로필 보기")
        print("  - /users: 모든 사용자 목록 보기")
        print("  - /logout: 로그아웃")
        print()
        print("채팅 기록 관리:")
        print("  - /history: 서버 채팅 기록 보기")
        print("  - /clear-server: 서버 채팅 기록 삭제")
        print()
        print("기타:")
        print("  - /test: 모든 API 엔드포인트 테스트")
        print("  - /help: 이 도움말 보기")
        print("  - /quit, /exit: 프로그램 종료")

    def chat_session(self):
        """메인 채팅 세션"""
        print(f"\n🤖 채팅을 시작합니다! ({self.current_user}님)")
        print("'/help'를 입력하면 명령어 도움말을 볼 수 있습니다.")
        print("-" * 50)

        while True:
            try:
                user_input = input(f"\n[{self.current_user}] ").strip()

                if not user_input:
                    continue

                # 종료 명령어
                if user_input.lower() in ["/quit", "/exit"]:
                    print("👋 채팅을 종료합니다. 안녕히 가세요!")
                    break

                # 로그아웃
                if user_input.lower() == "/logout":
                    if self.logout_user():
                        break
                    continue

                # 프로필 보기
                if user_input.lower() == "/profile":
                    self.get_user_profile()
                    continue

                # 사용자 목록 보기
                if user_input.lower() == "/users":
                    self.get_all_users()
                    continue

                # 채팅 기록 보기
                if user_input.lower() == "/history":
                    self.get_chat_history()
                    continue

                # 서버 채팅 기록 삭제
                if user_input.lower() == "/clear-server":
                    self.clear_chat_history()
                    continue

                # 전체 테스트
                if user_input.lower() == "/test":
                    self.test_all_endpoints()
                    continue

                # 도움말
                if user_input.lower() == "/help":
                    self.show_help()
                    continue

                # 역할 기반 채팅
                if user_input.startswith("/role "):
                    parts = user_input[6:].split(" ", 1)
                    if len(parts) >= 2:
                        role, message = parts[0], parts[1]
                        print(f"\n[{role}] ", end="", flush=True)
                        response = self.role_chat(role, message)
                        print(response)
                    else:
                        print("❌ 사용법: /role 역할명 메시지")
                    continue

                # 일반 채팅
                print("\n[AI] ", end="", flush=True)
                response = self.send_message(user_input)
                if response is None:  # 세션 만료
                    break
                print(response)

            except KeyboardInterrupt:
                print("\n\n👋 채팅을 종료합니다. 안녕히 가세요!")
                break
            except Exception as e:
                print(f"\n❌ 예상치 못한 오류: {e}")

    def run(self):
        """메인 실행 함수"""
        print("🚀 세션 기반 채팅 프로그램에 오신 것을 환영합니다!")

        # 서버 연결 확인
        try:
            response = self.session.get(self.server_url)
            if response.status_code != 200:
                print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
                return
        except requests.exceptions.RequestException:
            print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return

        while True:
            if not self.current_user:
                print("\n1. 회원가입")
                print("2. 로그인")
                print("3. 종료")

                choice = input("\n선택하세요 (1-3): ").strip()

                if choice == "1":
                    self.register_user()
                elif choice == "2":
                    if self.login_user():
                        self.chat_session()
                elif choice == "3":
                    print("👋 프로그램을 종료합니다.")
                    break
                else:
                    print("❌ 올바른 번호를 선택해주세요.")
            else:
                self.chat_session()
                self.current_user = None


def main():
    client = ChatClient()
    client.run()


if __name__ == "__main__":
    main()
