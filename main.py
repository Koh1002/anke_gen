import operator
import logging
from typing import Annotated, Any, Optional, List, Dict
from pathlib import Path
import os
import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
load_dotenv()

# 設定クラス
class Settings(BaseModel):
    openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY"))
    max_iterations: int = 2
    default_k: int = 10
    temperature: float = 0.7

settings = Settings()

# 調査要件を表すデータモデル
class SurveyRequirements(BaseModel):
    product_category: str = Field(..., description="商品カテゴリ")
    target_age_range: str = Field(..., description="ターゲット年齢層")
    target_gender: str = Field(..., description="ターゲット性別")
    survey_purpose: str = Field(..., description="調査目的")
    key_questions: List[str] = Field(..., description="主要な調査質問")
    additional_requirements: str = Field(default="", description="追加要件")

# 仮想ペルソナを表すデータモデル
class VirtualPersona(BaseModel):
    id: str = Field(..., description="ペルソナID")
    name: str = Field(..., description="ペルソナの名前")
    age: int = Field(..., description="年齢")
    gender: str = Field(..., description="性別")
    occupation: str = Field(..., description="職業")
    household_composition: str = Field(..., description="世帯構成")
    income_level: str = Field(..., description="所得レベル")
    lifestyle: str = Field(..., description="ライフスタイル")
    shopping_behavior: str = Field(..., description="購買行動")
    personality: str = Field(..., description="性格・特徴")
    background_story: str = Field(..., description="背景ストーリー")

# チャットメッセージを表すデータモデル
class ChatMessage(BaseModel):
    role: str = Field(..., description="メッセージの役割（user/assistant）")
    content: str = Field(..., description="メッセージ内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="タイムスタンプ")

# インタビューセッションを表すデータモデル
class InterviewSession(BaseModel):
    session_id: str = Field(..., description="セッションID")
    persona: VirtualPersona = Field(..., description="インタビュー対象のペルソナ")
    messages: List[ChatMessage] = Field(default_factory=list, description="チャットメッセージ")
    start_time: datetime = Field(default_factory=datetime.now, description="開始時刻")
    end_time: Optional[datetime] = Field(default=None, description="終了時刻")

# 固定質問インタビューを表すデータモデル
class FixedQuestionInterview(BaseModel):
    persona: VirtualPersona = Field(..., description="インタビュー対象のペルソナ")
    questions: List[str] = Field(..., description="質問リスト")
    answers: List[str] = Field(..., description="回答リスト")

# インタビュー結果のサマリーを表すデータモデル
class InterviewSummary(BaseModel):
    total_personas: int = Field(..., description="総ペルソナ数")
    total_interviews: int = Field(..., description="総インタビュー数")
    key_insights: List[str] = Field(..., description="主要な洞察")
    quantitative_results: Dict[str, Any] = Field(..., description="定量的結果")
    recommendations: List[str] = Field(..., description="推奨事項")

# システムのステート
class VirtualInterviewState(BaseModel):
    survey_requirements: Optional[SurveyRequirements] = Field(default=None, description="調査要件")
    personas: Annotated[List[VirtualPersona], operator.add] = Field(
        default_factory=list, description="生成されたペルソナのリスト"
    )
    chat_sessions: Annotated[List[InterviewSession], operator.add] = Field(
        default_factory=list, description="チャットインタビューセッション"
    )
    fixed_interviews: Annotated[List[FixedQuestionInterview], operator.add] = Field(
        default_factory=list, description="固定質問インタビュー"
    )
    summary: Optional[InterviewSummary] = Field(default=None, description="インタビュー結果サマリー")

# 調査要件ヒアリングクラス
class SurveyRequirementsCollector:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def get_template_questions(self) -> List[str]:
        """テンプレート質問を取得"""
        return [
            "調査したい商品カテゴリを教えてください（例：化粧品、食品、日用品など）",
            "ターゲットとする年齢層を教えてください（例：20-30代、30-40代など）",
            "ターゲットとする性別を教えてください（男性/女性/両方）",
            "調査の目的を教えてください（例：新商品開発、ブランド改善、市場参入など）",
            "特に知りたい点や調査したい内容を自由にお書きください"
        ]

    def parse_requirements(self, answers: List[str]) -> SurveyRequirements:
        """回答から調査要件を解析"""
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "あなたはマーケティング調査の専門家です。ユーザーの回答から調査要件を整理してください。"
            ),
            (
                "human",
                "以下の回答から調査要件を解析し、JSON形式で出力してください：\n\n"
                "回答1（商品カテゴリ）: {answer1}\n"
                "回答2（年齢層）: {answer2}\n"
                "回答3（性別）: {answer3}\n"
                "回答4（目的）: {answer4}\n"
                "回答5（追加要件）: {answer5}\n\n"
                "以下の形式で出力してください：\n"
                "{{\n"
                '  "product_category": "商品カテゴリ",\n'
                '  "target_age_range": "年齢層",\n'
                '  "target_gender": "性別",\n'
                '  "survey_purpose": "調査目的",\n'
                '  "key_questions": ["質問1", "質問2", "質問3"],\n'
                '  "additional_requirements": "追加要件"\n'
                "}}"
            )
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "answer1": answers[0],
            "answer2": answers[1],
            "answer3": answers[2],
            "answer4": answers[3],
            "answer5": answers[4]
        })
        
        try:
            data = json.loads(result)
            return SurveyRequirements(**data)
        except Exception as e:
            logger.error(f"Error parsing requirements: {str(e)}")
            # フォールバック
            return SurveyRequirements(
                product_category=answers[0],
                target_age_range=answers[1],
                target_gender=answers[2],
                survey_purpose=answers[3],
                key_questions=["商品の使用経験", "購買決定要因", "改善点"],
                additional_requirements=answers[4]
            )

# 仮想ペルソナ生成クラス
class VirtualPersonaGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_personas(self, requirements: SurveyRequirements, count: int = 5) -> List[VirtualPersona]:
        """調査要件に基づいて仮想ペルソナを生成"""
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "あなたはCPGメーカーのマーケティング調査で使用する仮想ペルソナを生成する専門家です。"
            ),
            (
                "human",
                "以下の調査要件に基づいて、{count}人の仮想ペルソナを生成してください：\n\n"
                "商品カテゴリ: {product_category}\n"
                "ターゲット年齢層: {target_age_range}\n"
                "ターゲット性別: {target_gender}\n"
                "調査目的: {survey_purpose}\n"
                "追加要件: {additional_requirements}\n\n"
                "各ペルソナは以下の形式で出力してください：\n"
                "ID: ユニークID\n"
                "名前: 姓名\n"
                "年齢: 数値\n"
                "性別: 男性/女性\n"
                "職業: 具体的な職業\n"
                "世帯構成: 家族構成\n"
                "所得レベル: 年収範囲\n"
                "ライフスタイル: 生活スタイル\n"
                "購買行動: 購買パターン\n"
                "性格・特徴: 性格や特徴\n"
                "背景ストーリー: 詳細な背景\n\n"
                "各ペルソナの間に空行を入れてください。"
            )
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "count": count,
            "product_category": requirements.product_category,
            "target_age_range": requirements.target_age_range,
            "target_gender": requirements.target_gender,
            "survey_purpose": requirements.survey_purpose,
            "additional_requirements": requirements.additional_requirements
        })
        
        personas = []
        sections = result.strip().split('\n\n')
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            try:
                persona_data = {}
                lines = section.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        persona_data[key.strip()] = value.strip()
                
                personas.append(VirtualPersona(
                    id=persona_data.get('ID', f"persona_{i+1}"),
                    name=persona_data.get('名前', f"ペルソナ{i+1}"),
                    age=int(persona_data.get('年齢', 30)),
                    gender=persona_data.get('性別', '女性'),
                    occupation=persona_data.get('職業', '会社員'),
                    household_composition=persona_data.get('世帯構成', '一人暮らし'),
                    income_level=persona_data.get('所得レベル', '300-500万円'),
                    lifestyle=persona_data.get('ライフスタイル', '普通'),
                    shopping_behavior=persona_data.get('購買行動', '月1回程度'),
                    personality=persona_data.get('性格・特徴', '慎重派'),
                    background_story=persona_data.get('背景ストーリー', '詳細な背景情報')
                ))
            except Exception as e:
                logger.error(f"Error parsing persona {i+1}: {str(e)}")
                continue
        
        return personas

# チャットインタビュー管理クラス
class ChatInterviewManager:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def create_session(self, persona: VirtualPersona) -> InterviewSession:
        """新しいチャットセッションを作成"""
        session_id = f"chat_{persona.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return InterviewSession(
            session_id=session_id,
            persona=persona
        )

    def get_persona_response(self, session: InterviewSession, user_message: str) -> str:
        """ペルソナの応答を生成"""
        # ペルソナの背景情報を構築
        persona_context = f"""
        あなたは以下のペルソナとして回答してください：
        
        名前: {session.persona.name}
        年齢: {session.persona.age}歳
        性別: {session.persona.gender}
        職業: {session.persona.occupation}
        世帯構成: {session.persona.household_composition}
        所得レベル: {session.persona.income_level}
        ライフスタイル: {session.persona.lifestyle}
        購買行動: {session.persona.shopping_behavior}
        性格・特徴: {session.persona.personality}
        背景ストーリー: {session.persona.background_story}
        
        このペルソナの立場から自然に回答してください。性格や背景を反映した回答を心がけてください。
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", persona_context),
            ("human", "{user_message}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"user_message": user_message})
        
        # セッションにメッセージを追加
        session.messages.append(ChatMessage(role="user", content=user_message))
        session.messages.append(ChatMessage(role="assistant", content=response))
        
        return response

# 固定質問インタビュー管理クラス
class FixedQuestionInterviewManager:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def conduct_interviews(self, personas: List[VirtualPersona], questions: List[str]) -> List[FixedQuestionInterview]:
        """複数のペルソナに対して固定質問でインタビューを実施"""
        interviews = []
        
        for persona in personas:
            answers = []
            for question in questions:
                answer = self._get_persona_answer(persona, question)
                answers.append(answer)
            
            interviews.append(FixedQuestionInterview(
                persona=persona,
                questions=questions,
                answers=answers
            ))
        
        return interviews

    def _get_persona_answer(self, persona: VirtualPersona, question: str) -> str:
        """個別のペルソナの回答を取得"""
        persona_context = f"""
        あなたは以下のペルソナとして回答してください：
        
        名前: {persona.name}
        年齢: {persona.age}歳
        性別: {persona.gender}
        職業: {persona.occupation}
        世帯構成: {persona.household_composition}
        所得レベル: {persona.income_level}
        ライフスタイル: {persona.lifestyle}
        購買行動: {persona.shopping_behavior}
        性格・特徴: {persona.personality}
        背景ストーリー: {persona.background_story}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", persona_context),
            ("human", "質問: {question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"question": question})

# インタビュー結果分析クラス
class InterviewAnalyzer:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_summary(self, state: VirtualInterviewState) -> InterviewSummary:
        """インタビュー結果のサマリーを生成"""
        # 定量的分析
        quantitative_results = self._analyze_quantitative_data(state)
        
        # 定性的分析
        key_insights = self._analyze_qualitative_data(state)
        
        # 推奨事項の生成
        recommendations = self._generate_recommendations(state, key_insights)
        
        return InterviewSummary(
            total_personas=len(state.personas),
            total_interviews=len(state.chat_sessions) + len(state.fixed_interviews),
            key_insights=key_insights,
            quantitative_results=quantitative_results,
            recommendations=recommendations
        )

    def _analyze_quantitative_data(self, state: VirtualInterviewState) -> Dict[str, Any]:
        """定量的データの分析"""
        results = {
            "demographics": {
                "age_distribution": {},
                "gender_distribution": {},
                "occupation_distribution": {}
            },
            "response_patterns": {}
        }
        
        # 年齢分布
        age_groups = {}
        for persona in state.personas:
            age_group = f"{(persona.age // 10) * 10}代"
            age_groups[age_group] = age_groups.get(age_group, 0) + 1
        results["demographics"]["age_distribution"] = age_groups
        
        # 性別分布
        gender_counts = {}
        for persona in state.personas:
            gender_counts[persona.gender] = gender_counts.get(persona.gender, 0) + 1
        results["demographics"]["gender_distribution"] = gender_counts
        
        # 職業分布
        occupation_counts = {}
        for persona in state.personas:
            occupation_counts[persona.occupation] = occupation_counts.get(persona.occupation, 0) + 1
        results["demographics"]["occupation_distribution"] = occupation_counts
        
        return results

    def _analyze_qualitative_data(self, state: VirtualInterviewState) -> List[str]:
        """定性的データの分析"""
        # チャットセッションと固定インタビューの内容を統合
        all_content = []
        
        for session in state.chat_sessions:
            for message in session.messages:
                if message.role == "assistant":
                    all_content.append(message.content)
        
        for interview in state.fixed_interviews:
            all_content.extend(interview.answers)
        
        # AIによる洞察の抽出
        content_text = "\n".join(all_content)
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "あなたはマーケティング調査の専門家です。インタビュー結果から主要な洞察を抽出してください。"
            ),
            (
                "human",
                "以下のインタビュー結果から、マーケティング戦略に活用できる主要な洞察を5つ抽出してください：\n\n"
                "{content}\n\n"
                "各洞察は具体的で実用的な内容にしてください。"
            )
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({"content": content_text})
        
        # 結果をリストに分割
        insights = [line.strip() for line in result.split('\n') if line.strip()]
        return insights[:5]  # 最大5つまで

    def _generate_recommendations(self, state: VirtualInterviewState, insights: List[str]) -> List[str]:
        """推奨事項の生成"""
        insights_text = "\n".join(insights)
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "あなたはマーケティング戦略の専門家です。調査結果に基づいて具体的な推奨事項を提案してください。"
            ),
            (
                "human",
                "以下の洞察に基づいて、CPGメーカー向けの具体的な推奨事項を3つ提案してください：\n\n"
                "洞察:\n{insights}\n\n"
                "商品カテゴリ: {product_category}\n"
                "調査目的: {survey_purpose}\n\n"
                "各推奨事項は具体的で実行可能な内容にしてください。"
            )
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "insights": insights_text,
            "product_category": state.survey_requirements.product_category if state.survey_requirements else "",
            "survey_purpose": state.survey_requirements.survey_purpose if state.survey_requirements else ""
        })
        
        recommendations = [line.strip() for line in result.split('\n') if line.strip()]
        return recommendations[:3]  # 最大3つまで

# グラフ生成クラス
class ChartGenerator:
    def __init__(self):
        # 日本語フォント設定
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
        sns.set_style("whitegrid")

    def generate_demographics_charts(self, summary: InterviewSummary) -> Dict[str, str]:
        """人口統計チャートを生成"""
        charts = {}
        
        # 年齢分布チャート
        age_data = summary.quantitative_results["demographics"]["age_distribution"]
        if age_data:
            plt.figure(figsize=(10, 6))
            plt.bar(age_data.keys(), age_data.values(), color='skyblue')
            plt.title('年齢分布', fontsize=14, fontweight='bold')
            plt.xlabel('年齢層')
            plt.ylabel('人数')
            plt.xticks(rotation=45)
            
            # グラフをBase64エンコード
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            buffer.seek(0)
            charts['age_distribution'] = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
        
        # 性別分布チャート
        gender_data = summary.quantitative_results["demographics"]["gender_distribution"]
        if gender_data:
            plt.figure(figsize=(8, 8))
            plt.pie(gender_data.values(), labels=gender_data.keys(), autopct='%1.1f%%', startangle=90)
            plt.title('性別分布', fontsize=14, fontweight='bold')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            buffer.seek(0)
            charts['gender_distribution'] = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
        
        return charts

# メインの仮想インタビューシステム
class VirtualInterviewSystem:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.requirements_collector = SurveyRequirementsCollector(llm)
        self.persona_generator = VirtualPersonaGenerator(llm)
        self.chat_manager = ChatInterviewManager(llm)
        self.fixed_interview_manager = FixedQuestionInterviewManager(llm)
        self.analyzer = InterviewAnalyzer(llm)
        self.chart_generator = ChartGenerator()
        self.state = VirtualInterviewState()
        logger.info("VirtualInterviewSystem initialized")

    def collect_survey_requirements(self, answers: List[str]) -> SurveyRequirements:
        """調査要件の収集"""
        requirements = self.requirements_collector.parse_requirements(answers)
        self.state.survey_requirements = requirements
        return requirements

    def generate_personas(self, count: int = 5) -> List[VirtualPersona]:
        """ペルソナの生成"""
        if not self.state.survey_requirements:
            raise ValueError("Survey requirements not set")
        
        personas = self.persona_generator.generate_personas(
            self.state.survey_requirements, count
        )
        self.state.personas.extend(personas)
        return personas

    def start_chat_session(self, persona_id: str) -> InterviewSession:
        """チャットセッションの開始"""
        persona = next((p for p in self.state.personas if p.id == persona_id), None)
        if not persona:
            raise ValueError(f"Persona with ID {persona_id} not found")
        
        session = self.chat_manager.create_session(persona)
        self.state.chat_sessions.append(session)
        return session

    def send_chat_message(self, session_id: str, message: str) -> str:
        """チャットメッセージの送信"""
        session = next((s for s in self.state.chat_sessions if s.session_id == session_id), None)
        if not session:
            raise ValueError(f"Session with ID {session_id} not found")
        
        return self.chat_manager.get_persona_response(session, message)

    def conduct_fixed_interviews(self, persona_ids: List[str], questions: List[str]) -> List[FixedQuestionInterview]:
        """固定質問インタビューの実施"""
        selected_personas = [p for p in self.state.personas if p.id in persona_ids]
        interviews = self.fixed_interview_manager.conduct_interviews(selected_personas, questions)
        self.state.fixed_interviews.extend(interviews)
        return interviews

    def generate_summary(self) -> Dict[str, Any]:
        """結果サマリーの生成"""
        summary = self.analyzer.generate_summary(self.state)
        self.state.summary = summary
        
        # チャートの生成
        charts = self.chart_generator.generate_demographics_charts(summary)
        
        return {
            "summary": summary,
            "charts": charts,
            "state": self.state
        }

    def export_to_excel(self, filename: str = None) -> str:
        """結果をExcelファイルに出力"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"virtual_interview_results_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 調査要件シート
            if self.state.survey_requirements:
                req_data = {
                    "項目": ["商品カテゴリ", "ターゲット年齢層", "ターゲット性別", "調査目的", "追加要件"],
                    "内容": [
                        self.state.survey_requirements.product_category,
                        self.state.survey_requirements.target_age_range,
                        self.state.survey_requirements.target_gender,
                        self.state.survey_requirements.survey_purpose,
                        self.state.survey_requirements.additional_requirements
                    ]
                }
                pd.DataFrame(req_data).to_excel(writer, sheet_name='調査要件', index=False)
            
            # ペルソナ情報シート
            if self.state.personas:
                persona_data = []
                for persona in self.state.personas:
                    persona_data.append({
                        "ID": persona.id,
                        "名前": persona.name,
                        "年齢": persona.age,
                        "性別": persona.gender,
                        "職業": persona.occupation,
                        "世帯構成": persona.household_composition,
                        "所得レベル": persona.income_level,
                        "ライフスタイル": persona.lifestyle,
                        "購買行動": persona.shopping_behavior,
                        "性格・特徴": persona.personality
                    })
                pd.DataFrame(persona_data).to_excel(writer, sheet_name='ペルソナ情報', index=False)
            
            # チャットインタビュー結果シート
            if self.state.chat_sessions:
                chat_data = []
                for session in self.state.chat_sessions:
                    for message in session.messages:
                        chat_data.append({
                            "セッションID": session.session_id,
                            "ペルソナ": session.persona.name,
                            "役割": message.role,
                            "メッセージ": message.content,
                            "タイムスタンプ": message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        })
                pd.DataFrame(chat_data).to_excel(writer, sheet_name='チャットインタビュー', index=False)
            
            # 固定質問インタビュー結果シート
            if self.state.fixed_interviews:
                fixed_data = []
                for interview in self.state.fixed_interviews:
                    for i, (question, answer) in enumerate(zip(interview.questions, interview.answers)):
                        fixed_data.append({
                            "ペルソナ": interview.persona.name,
                            "質問番号": i + 1,
                            "質問": question,
                            "回答": answer
                        })
                pd.DataFrame(fixed_data).to_excel(writer, sheet_name='固定質問インタビュー', index=False)
            
            # サマリーシート
            if self.state.summary:
                summary_data = {
                    "項目": ["総ペルソナ数", "総インタビュー数"],
                    "数値": [self.state.summary.total_personas, self.state.summary.total_interviews]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='サマリー', index=False)
                
                # 主要洞察
                insights_data = {"洞察": self.state.summary.key_insights}
                pd.DataFrame(insights_data).to_excel(writer, sheet_name='主要洞察', index=False)
                
                # 推奨事項
                rec_data = {"推奨事項": self.state.summary.recommendations}
                pd.DataFrame(rec_data).to_excel(writer, sheet_name='推奨事項', index=False)
        
        return filename

def main():
    try:
        logger.info("Initializing Virtual Interview System")
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
        )
        system = VirtualInterviewSystem(llm=llm)
        logger.info("Virtual Interview System initialized successfully")
        return system
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
