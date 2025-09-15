import requests
import json
import sys
from typing import List, Dict


class ChatClient:
    def __init__(self, server_url="http://127.0.0.1:8000"):
        self.server_url = server_url
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
            response = requests.post(
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
        """사용자 로그인"""
        print("\n=== 로그인 ===")
        username = input("사용자명을 입력하세요: ").strip()
        password = input("비밀번호를 입력하세요: ").strip()

        if not username or not password:
            print("사용자명과 비밀번호를 모두 입력해주세요.")
            return False

        try:
            response = requests.post(
                f"{self.server_url}/user/login",
                json={"username": username, "password": password},
            )

            if response.status_code == 200:
                self.current_user = username
                print(f"✅ 로그인 성공! 환영합니다, {username}님!")
                return True
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                print(f"❌ 로그인 실패: {error_detail}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def send_message(self, user_message):
        """메시지 전송 및 AI 응답 받기"""
        # 대화 기록에 사용자 메시지 추가
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = requests.post(
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
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                return f"❌ 오류: {error_detail}"

        except requests.exceptions.RequestException as e:
            return f"❌ 서버 연결 오류: {e}"

    def role_chat(self, role, message):
        """역할 기반 채팅"""
        try:
            response = requests.post(
                f"{self.server_url}/chat/role",
                params={"role": role, "message": message},
            )

            if response.status_code == 200:
                result = response.json()
                return result["ai_response"]
            else:
                error_detail = response.json().get("detail", "알 수 없는 오류")
                return f"❌ 오류: {error_detail}"

        except requests.exceptions.RequestException as e:
            return f"❌ 서버 연결 오류: {e}"

    def chat_session(self):
        """메인 채팅 세션"""
        print(f"\n🤖 채팅을 시작합니다! ({self.current_user}님)")
        print("도움말:")
        print("- 일반 채팅: 그냥 메시지를 입력하세요")
        print("- 역할 채팅: '/role 역할명 메시지' (예: /role 시인 봄에 대해 써줘)")
        print("- 대화 기록 초기화: '/clear'")
        print("- 종료: '/quit' 또는 '/exit'")
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

                # 대화 기록 초기화
                if user_input.lower() == "/clear":
                    self.conversation_history = []
                    print("🗑️ 대화 기록이 초기화되었습니다.")
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
                print(response)

            except KeyboardInterrupt:
                print("\n\n👋 채팅을 종료합니다. 안녕히 가세요!")
                break
            except Exception as e:
                print(f"\n❌ 예상치 못한 오류: {e}")

    def run(self):
        """메인 실행 함수"""
        print("🚀 채팅 프로그램에 오신 것을 환영합니다!")

        # 서버 연결 확인
        try:
            response = requests.get(self.server_url)
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
                self.current_user = None  # 로그아웃


def main():
    client = ChatClient()
    client.run()


if __name__ == "__main__":
    main()
