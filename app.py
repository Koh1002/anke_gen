from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
from typing import List, Dict, Any, Optional
import json
import os
from main import VirtualInterviewSystem, ChatOpenAI, settings, SurveyRequirements
from dotenv import load_dotenv
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
load_dotenv()

app = FastAPI(title="仮想インタビューシステム", version="2.0.0")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class SurveyRequirementsRequest(BaseModel):
    answers: List[str]

class GeneratePersonasRequest(BaseModel):
    count: int = 5

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class FixedInterviewRequest(BaseModel):
    persona_ids: List[str]
    questions: List[str]

# レスポンスモデル
class SurveyRequirementsResponse(BaseModel):
    requirements: Dict[str, Any]

class PersonasResponse(BaseModel):
    personas: List[Dict[str, Any]]

class ChatSessionResponse(BaseModel):
    session: Dict[str, Any]

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str

class FixedInterviewResponse(BaseModel):
    interviews: List[Dict[str, Any]]

class SummaryResponse(BaseModel):
    summary: Dict[str, Any]
    charts: Dict[str, str]

# OpenAI APIキーの設定
# 環境変数からAPIキーを読み込む
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set your OpenAI API key in the .env file or environment variables.")

# 設定を更新
settings.openai_api_key = api_key

# 仮想インタビューシステムのインスタンス化
try:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=settings.temperature,
        api_key=settings.openai_api_key,
    )
    interview_system = VirtualInterviewSystem(llm=llm)
except Exception as e:
    raise ValueError(f"Failed to initialize Virtual Interview System: {str(e)}")

@app.get("/")
async def root():
    return {"message": "仮想インタビューシステム API v2.0.0"}

@app.get("/template-questions")
async def get_template_questions():
    """テンプレート質問を取得"""
    return {
        "questions": [
            "調査したい商品カテゴリを教えてください（例：化粧品、食品、日用品など）",
            "ターゲットとする年齢層を教えてください（例：20-30代、30-40代など）",
            "ターゲットとする性別を教えてください（男性/女性/両方）",
            "調査の目的を教えてください（例：新商品開発、ブランド改善、市場参入など）",
            "特に知りたい点や調査したい内容を自由にお書きください"
        ]
    }

@app.post("/collect-requirements", response_model=SurveyRequirementsResponse)
async def collect_survey_requirements(request: SurveyRequirementsRequest):
    """調査要件の収集"""
    try:
        requirements = interview_system.collect_survey_requirements(request.answers)
        return SurveyRequirementsResponse(
            requirements={
                "product_category": requirements.product_category,
                "target_age_range": requirements.target_age_range,
                "target_gender": requirements.target_gender,
                "survey_purpose": requirements.survey_purpose,
                "key_questions": requirements.key_questions,
                "additional_requirements": requirements.additional_requirements
            }
        )
    except Exception as e:
        logger.error(f"Error in collect_survey_requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-personas", response_model=PersonasResponse)
async def generate_personas(request: GeneratePersonasRequest):
    """ペルソナの生成"""
    try:
        personas = interview_system.generate_personas(request.count)
        return PersonasResponse(
            personas=[
                {
                    "id": persona.id,
                    "name": persona.name,
                    "age": persona.age,
                    "gender": persona.gender,
                    "occupation": persona.occupation,
                    "household_composition": persona.household_composition,
                    "income_level": persona.income_level,
                    "lifestyle": persona.lifestyle,
                    "shopping_behavior": persona.shopping_behavior,
                    "personality": persona.personality,
                    "background_story": persona.background_story
                }
                for persona in personas
            ]
        )
    except Exception as e:
        logger.error(f"Error in generate_personas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-chat-session", response_model=ChatSessionResponse)
async def start_chat_session(persona_id: str):
    """チャットセッションの開始"""
    try:
        session = interview_system.start_chat_session(persona_id)
        return ChatSessionResponse(
            session={
                "session_id": session.session_id,
                "persona": {
                    "id": session.persona.id,
                    "name": session.persona.name,
                    "age": session.persona.age,
                    "gender": session.persona.gender,
                    "occupation": session.persona.occupation,
                    "background_story": session.persona.background_story
                },
                "start_time": session.start_time.isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error in start_chat_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-chat-message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """チャットメッセージの送信"""
    try:
        response = interview_system.send_chat_message(request.session_id, request.message)
        return ChatMessageResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        logger.error(f"Error in send_chat_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conduct-fixed-interviews", response_model=FixedInterviewResponse)
async def conduct_fixed_interviews(request: FixedInterviewRequest):
    """固定質問インタビューの実施"""
    try:
        interviews = interview_system.conduct_fixed_interviews(request.persona_ids, request.questions)
        return FixedInterviewResponse(
            interviews=[
                {
                    "persona": {
                        "id": interview.persona.id,
                        "name": interview.persona.name,
                        "age": interview.persona.age,
                        "gender": interview.persona.gender,
                        "occupation": interview.persona.occupation
                    },
                    "questions": interview.questions,
                    "answers": interview.answers
                }
                for interview in interviews
            ]
        )
    except Exception as e:
        logger.error(f"Error in conduct_fixed_interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-summary", response_model=SummaryResponse)
async def generate_summary():
    """結果サマリーの生成"""
    try:
        result = interview_system.generate_summary()
        return SummaryResponse(
            summary={
                "total_personas": result["summary"].total_personas,
                "total_interviews": result["summary"].total_interviews,
                "key_insights": result["summary"].key_insights,
                "quantitative_results": result["summary"].quantitative_results,
                "recommendations": result["summary"].recommendations
            },
            charts=result["charts"]
        )
    except Exception as e:
        logger.error(f"Error in generate_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-excel/{filename}")
async def download_excel(filename: str):
    """Excelファイルのダウンロード"""
    try:
        file_path = os.path.join("output", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export-excel")
async def export_excel():
    """Excelファイルの出力"""
    try:
        filename = interview_system.export_to_excel()
        return {"file_path": filename, "message": "Excel file exported successfully"}
    except Exception as e:
        logger.error(f"Error in export_excel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-personas")
async def get_personas():
    """生成されたペルソナ一覧を取得"""
    try:
        return {
            "personas": [
                {
                    "id": persona.id,
                    "name": persona.name,
                    "age": persona.age,
                    "gender": persona.gender,
                    "occupation": persona.occupation,
                    "household_composition": persona.household_composition,
                    "income_level": persona.income_level,
                    "lifestyle": persona.lifestyle,
                    "shopping_behavior": persona.shopping_behavior,
                    "personality": persona.personality,
                    "background_story": persona.background_story
                }
                for persona in interview_system.state.personas
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_personas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-chat-sessions")
async def get_chat_sessions():
    """チャットセッション一覧を取得"""
    try:
        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "persona": {
                        "id": session.persona.id,
                        "name": session.persona.name,
                        "age": session.persona.age,
                        "gender": session.persona.gender,
                        "occupation": session.persona.occupation
                    },
                    "message_count": len(session.messages),
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None
                }
                for session in interview_system.state.chat_sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_chat_sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 