import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()


def get_firestore_db():
    """
    Firebase Firestore 클라이언트를 안전하게 초기화하고 반환합니다.
    1. FIREBASE_SERVICE_ACCOUNT_JSON_RAW (클라우드 환경 변수에 JSON 문자열을 직접 넣는 경우)
    2. FIREBASE_SERVICE_ACCOUNT_JSON (키 파일 경로 환경 변수)
    3. 'serviceAccountKey.json' (로컬 기본 파일 경로)
    4. Google Cloud 기본 인증 (Application Default Credentials)
    순서로 인증을 탐색합니다.
    """
    if firebase_admin._apps:
        return firestore.client()

    # 1. 환경 변수에 JSON 문자열이 직접 저장된 경우 (Render 등 배포 시 유용)
    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_RAW")
    if raw_json:
        try:
            cred_dict = json.loads(raw_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            print(f"[경고] FIREBASE_SERVICE_ACCOUNT_JSON_RAW 파싱 실패: {e}")

    # 2. 파일 경로 지정 (환경변수 또는 로컬 기본 파일)
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "serviceAccountKey.json")
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()

    # 3. Google Cloud 기본 애플리케이션 인증 폴백
    try:
        firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        raise RuntimeError(
            f"Firebase 초기화 실패: 인증 키를 찾을 수 없습니다. ({key_path})\n"
            "serviceAccountKey.json 파일을 프로젝트 루트에 배치하거나 "
            "FIREBASE_SERVICE_ACCOUNT_JSON 또는 FIREBASE_SERVICE_ACCOUNT_JSON_RAW 환경변수를 설정해 주세요."
        ) from e
