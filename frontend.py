import streamlit as st
import requests
import pandas as pd
import json
import base64
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="仮想インタビューシステム",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイル設定
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .persona-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f3e5f5;
        margin-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'requirements'
if 'survey_requirements' not in st.session_state:
    st.session_state.survey_requirements = None
if 'personas' not in st.session_state:
    st.session_state.personas = []
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'fixed_interviews' not in st.session_state:
    st.session_state.fixed_interviews = []
if 'summary' not in st.session_state:
    st.session_state.summary = None

# API設定
API_BASE_URL = "http://localhost:8000"

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None):
    """APIリクエストの共通関数"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"APIエラー: {str(e)}")
        return None

# メインタイトル
st.markdown('<h1 class="main-header">🎭 仮想インタビューシステム</h1>', unsafe_allow_html=True)

# サイドバー - ナビゲーション
with st.sidebar:
    st.header("📋 ナビゲーション")
    
    # ステップ表示
    steps = [
        ("requirements", "1. 調査要件の収集"),
        ("personas", "2. ペルソナ生成"),
        ("interview", "3. インタビュー実施"),
        ("summary", "4. 結果サマリー")
    ]
    
    for step_id, step_name in steps:
        if st.session_state.current_step == step_id:
            st.markdown(f"**{step_name}** ✅")
        else:
            st.markdown(step_name)
    
    st.divider()
    
    # システム情報
    st.header("ℹ️ システム情報")
    st.info("CPGメーカー向け仮想インタビューシステム")
    st.caption("Version 2.0.0")

# ステップ1: 調査要件の収集
if st.session_state.current_step == 'requirements':
    st.markdown('<h2 class="section-header">📝 調査要件の収集</h2>', unsafe_allow_html=True)
    
    # テンプレート質問の取得
    template_data = make_api_request("/template-questions")
    
    if template_data:
        questions = template_data["questions"]
        
        st.write("以下の質問にお答えください。調査に最適なペルソナを生成するために使用します。")
        
        # 質問フォーム
        with st.form("requirements_form"):
            answers = []
            for i, question in enumerate(questions):
                if i < len(questions) - 1:
                    # 通常の質問
                    answer = st.text_input(f"質問{i+1}: {question}", key=f"q{i}")
                    answers.append(answer)
                else:
                    # 最後の自由記述
                    answer = st.text_area(f"質問{i+1}: {question}", key=f"q{i}", height=100)
                    answers.append(answer)
            
            submitted = st.form_submit_button("要件を送信", type="primary")
            
            if submitted:
                if all(answers):
                    with st.spinner("調査要件を処理中..."):
                        result = make_api_request("/collect-requirements", "POST", {"answers": answers})
                        if result:
                            st.session_state.survey_requirements = result["requirements"]
                            st.session_state.current_step = 'personas'
                            st.success("調査要件が正常に処理されました！")
                            st.rerun()
                else:
                    st.error("すべての質問にお答えください。")

# ステップ2: ペルソナ生成
elif st.session_state.current_step == 'personas':
    st.markdown('<h2 class="section-header">👥 ペルソナ生成</h2>', unsafe_allow_html=True)
    
    # 調査要件の表示
    if st.session_state.survey_requirements:
        st.subheader("📋 調査要件")
        req = st.session_state.survey_requirements
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**商品カテゴリ:** {req['product_category']}")
            st.write(f"**ターゲット年齢層:** {req['target_age_range']}")
            st.write(f"**ターゲット性別:** {req['target_gender']}")
        with col2:
            st.write(f"**調査目的:** {req['survey_purpose']}")
            st.write(f"**追加要件:** {req['additional_requirements']}")
    
    # ペルソナ生成
    if not st.session_state.personas:
        st.subheader("🎭 ペルソナを生成")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            persona_count = st.number_input("生成するペルソナ数", min_value=3, max_value=10, value=5)
            if st.button("ペルソナを生成", type="primary"):
                with st.spinner("ペルソナを生成中..."):
                    result = make_api_request("/generate-personas", "POST", {"count": persona_count})
                    if result:
                        st.session_state.personas = result["personas"]
                        st.success(f"{len(result['personas'])}人のペルソナが生成されました！")
                        st.rerun()
    
    # 生成されたペルソナの表示
    if st.session_state.personas:
        st.subheader("👥 生成されたペルソナ")
        
        for i, persona in enumerate(st.session_state.personas):
            with st.expander(f"👤 {persona['name']} ({persona['age']}歳, {persona['gender']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**職業:** {persona['occupation']}")
                    st.write(f"**世帯構成:** {persona['household_composition']}")
                    st.write(f"**所得レベル:** {persona['income_level']}")
                    st.write(f"**ライフスタイル:** {persona['lifestyle']}")
                with col2:
                    st.write(f"**購買行動:** {persona['shopping_behavior']}")
                    st.write(f"**性格・特徴:** {persona['personality']}")
                
                st.write("**背景ストーリー:**")
                st.write(persona['background_story'])
        
        # 次のステップへ
        if st.button("インタビューを開始", type="primary"):
            st.session_state.current_step = 'interview'
            st.rerun()

# ステップ3: インタビュー実施
elif st.session_state.current_step == 'interview':
    st.markdown('<h2 class="section-header">💬 インタビュー実施</h2>', unsafe_allow_html=True)
    
    # インタビュー方法の選択
    interview_method = st.radio(
        "インタビュー方法を選択してください",
        ["チャットインタビュー", "固定質問インタビュー"],
        horizontal=True
    )
    
    if interview_method == "チャットインタビュー":
        st.subheader("💬 チャットインタビュー")
        
        # ペルソナ選択
        if st.session_state.personas:
            persona_names = [f"{p['name']} ({p['age']}歳, {p['gender']})" for p in st.session_state.personas]
            selected_persona_idx = st.selectbox("インタビューするペルソナを選択", range(len(persona_names)), format_func=lambda x: persona_names[x])
            
            if st.button("チャットセッションを開始", type="primary"):
                selected_persona = st.session_state.personas[selected_persona_idx]
                with st.spinner("セッションを開始中..."):
                    result = make_api_request(f"/start-chat-session?persona_id={selected_persona['id']}", "POST")
                    if result:
                        st.session_state.current_session = result["session"]
                        st.session_state.chat_messages = []
                        st.success(f"{selected_persona['name']}とのチャットセッションを開始しました！")
                        st.rerun()
            
            # チャットインターフェース
            if st.session_state.current_session:
                st.subheader(f"💬 {st.session_state.current_session['persona']['name']}とのチャット")
                
                # チャット履歴の表示
                chat_container = st.container()
                with chat_container:
                    for message in st.session_state.chat_messages:
                        if message['role'] == 'user':
                            st.markdown(f'<div class="chat-message user-message">👤 **あなた:** {message["content"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message assistant-message">🎭 **{st.session_state.current_session["persona"]["name"]}:** {message["content"]}</div>', unsafe_allow_html=True)
                
                # メッセージ送信
                with st.form("chat_form"):
                    user_message = st.text_input("メッセージを入力", key="chat_input")
                    send_button = st.form_submit_button("送信", type="primary")
                    
                    if send_button and user_message:
                        # ユーザーメッセージを追加
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": user_message
                        })
                        
                        # APIに送信
                        with st.spinner("応答を生成中..."):
                            result = make_api_request("/send-chat-message", "POST", {
                                "session_id": st.session_state.current_session["session_id"],
                                "message": user_message
                            })
                            if result:
                                # ペルソナの応答を追加
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": result["response"]
                                })
                                st.rerun()
    
    else:  # 固定質問インタビュー
        st.subheader("📋 固定質問インタビュー")
        
        # ペルソナ選択
        if st.session_state.personas:
            selected_personas = st.multiselect(
                "インタビューするペルソナを選択",
                options=st.session_state.personas,
                format_func=lambda x: f"{x['name']} ({x['age']}歳, {x['gender']})"
            )
            
            # 質問入力
            st.write("インタビューする質問を入力してください（1行に1つの質問）")
            questions_text = st.text_area("質問", height=150, placeholder="例：\nこの商品カテゴリについてどのような印象をお持ちですか？\n購入する際に最も重視する点は何ですか？\n改善してほしい点はありますか？")
            
            if st.button("インタビューを実行", type="primary") and selected_personas and questions_text:
                questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
                persona_ids = [p['id'] for p in selected_personas]
                
                with st.spinner("インタビューを実行中..."):
                    result = make_api_request("/conduct-fixed-interviews", "POST", {
                        "persona_ids": persona_ids,
                        "questions": questions
                    })
                    if result:
                        st.session_state.fixed_interviews = result["interviews"]
                        st.success(f"{len(selected_personas)}人のペルソナに{len(questions)}個の質問でインタビューを完了しました！")
                        st.rerun()
        
        # インタビュー結果の表示
        if st.session_state.fixed_interviews:
            st.subheader("📊 インタビュー結果")
            
            for interview in st.session_state.fixed_interviews:
                with st.expander(f"👤 {interview['persona']['name']}の回答"):
                    for i, (question, answer) in enumerate(zip(interview['questions'], interview['answers'])):
                        st.write(f"**質問{i+1}:** {question}")
                        st.write(f"**回答:** {answer}")
                        st.divider()
    
    # サマリー生成へ
    if st.button("結果サマリーを生成", type="primary"):
        st.session_state.current_step = 'summary'
        st.rerun()

# ステップ4: 結果サマリー
elif st.session_state.current_step == 'summary':
    st.markdown('<h2 class="section-header">📊 結果サマリー</h2>', unsafe_allow_html=True)
    
    if st.button("サマリーを生成", type="primary"):
        with st.spinner("サマリーを生成中..."):
            result = make_api_request("/generate-summary", "POST")
            if result:
                st.session_state.summary = result
                st.success("サマリーが生成されました！")
                st.rerun()
    
    if st.session_state.summary:
        summary = st.session_state.summary["summary"]
        charts = st.session_state.summary["charts"]
        
        # 基本統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総ペルソナ数", summary["total_personas"])
        with col2:
            st.metric("総インタビュー数", summary["total_interviews"])
        with col3:
            st.metric("生成日時", datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # チャート表示
        if charts:
            st.subheader("📈 人口統計")
            col1, col2 = st.columns(2)
            
            with col1:
                if 'age_distribution' in charts:
                    st.image(f"data:image/png;base64,{charts['age_distribution']}", caption="年齢分布")
            
            with col2:
                if 'gender_distribution' in charts:
                    st.image(f"data:image/png;base64,{charts['gender_distribution']}", caption="性別分布")
        
        # 主要洞察
        st.subheader("💡 主要洞察")
        for i, insight in enumerate(summary["key_insights"], 1):
            st.write(f"{i}. {insight}")
        
        # 推奨事項
        st.subheader("🎯 推奨事項")
        for i, recommendation in enumerate(summary["recommendations"], 1):
            st.write(f"{i}. {recommendation}")
        
        # Excel出力
        if st.button("Excelファイルを出力", type="primary"):
            with st.spinner("Excelファイルを生成中..."):
                result = make_api_request("/export-excel", "POST")
                if result:
                    st.success("Excelファイルが生成されました！")
                    
                    # ダウンロードボタン
                    filename = result["file_path"]
                    try:
                        with open(filename, "rb") as f:
                            st.download_button(
                                label="Excelファイルをダウンロード",
                                data=f.read(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except FileNotFoundError:
                        st.error("ファイルが見つかりませんでした。")

# フッター
st.divider()
st.caption("© 2024 仮想インタビューシステム v2.0.0") 