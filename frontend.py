import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import plotly.express as px

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
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# API設定 - Streamlit Cloud環境では直接処理
def is_streamlit_cloud():
    """Streamlit Cloud環境かどうかを判定"""
    try:
        import os
        
        # 最も確実な判定：OPENAI_API_KEY環境変数の存在確認
        if 'OPENAI_API_KEY' in os.environ:
            return True
        
        # 環境変数で判定（Streamlit Cloud特有の環境変数）
        if 'STREAMLIT_CLOUD_ENVIRONMENT' in os.environ:
            return True
        
        # より確実な判定：st.secretsの存在確認
        if hasattr(st, 'secrets') and st.secrets is not None:
            try:
                # secretsが存在し、かつ何らかの値が設定されている場合はStreamlit Cloudと判断
                if hasattr(st.secrets, '_secrets') and len(st.secrets._secrets) > 0:
                    return True
                # 直接アクセス可能な場合
                if hasattr(st.secrets, 'get') and callable(getattr(st.secrets, 'get')):
                    return True
            except Exception:
                pass
        
        # ホスト名で判定（最後の手段）
        import socket
        hostname = socket.gethostname()
        if 'streamlit' in hostname.lower() or 'cloud' in hostname.lower():
            return True
        
        # ローカル環境と判断
        return False
    except Exception:
        # エラーが発生した場合はローカル環境と判断
        return False

# ローカル環境でのみAPIを使用
API_BASE_URL = "http://localhost:8000" if not is_streamlit_cloud() else None

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None):
    """APIリクエストの共通関数（ローカル環境用）"""
    if is_streamlit_cloud():
        st.error("Streamlit Cloud環境では、この機能は現在利用できません。")
        return None
    
    try:
        # ローカル環境でのみrequestsを使用
        import requests
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except ImportError:
        st.error("requestsライブラリが利用できません。ローカル環境で実行してください。")
        return None
    except Exception as e:
        st.error(f"APIエラー: {str(e)}")
        return None

# メインタイトル
st.markdown('<h1 class="main-header">🎭 仮想インタビューシステム</h1>', unsafe_allow_html=True)

# サイドバー - ナビゲーション
with st.sidebar:
    st.header("📋 ナビゲーション")
    
    # APIキーの設定状況を表示
    st.subheader("🔑 API設定状況")
    
    if is_streamlit_cloud():
        try:
            # Streamlit Cloud環境でのAPIキー確認
            if hasattr(st, 'secrets') and st.secrets is not None:
                if 'OPENAI_API_KEY' in st.secrets:
                    st.success("✅ OpenAI APIキーが設定されています")
                else:
                    st.warning("⚠️ OpenAI APIキーが設定されていません")
                    st.info("Streamlit Cloudのsecretsで設定してください")
            else:
                st.error("❌ st.secretsが利用できません")
        except Exception:
            st.warning("⚠️ API設定の確認に失敗しました")
    else:
        st.info("ℹ️ ローカル環境で実行中")
        # ローカル環境でのAPIキー確認
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            if os.getenv('OPENAI_API_KEY'):
                st.success("✅ ローカル環境でOpenAI APIキーが設定されています")
            else:
                st.warning("⚠️ ローカル環境でOpenAI APIキーが設定されていません")
                st.info(".envファイルにOPENAI_API_KEYを設定してください")
        except:
            st.info("ℹ️ .envファイルの読み込みに失敗しました")
    
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
    
    # テンプレート質問（Streamlit Cloud環境用）
    questions = [
        "調査したい商品カテゴリを教えてください（例：化粧品、食品、日用品など）",
        "ターゲットとする年齢層を教えてください（例：20-30代、30-40代など）",
        "ターゲットとする性別を教えてください（男性/女性/両方）",
        "調査の目的を教えてください（例：新商品開発、ブランド改善、市場参入など）",
        "特に知りたい点や調査したい内容を自由にお書きください"
    ]
    
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
                # 調査要件を直接処理
                survey_requirements = {
                    "product_category": answers[0],
                    "target_age_range": answers[1],
                    "target_gender": answers[2],
                    "survey_purpose": answers[3],
                    "additional_requirements": answers[4]
                }
                st.session_state.survey_requirements = survey_requirements
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
                    # GPT APIキーが設定されている場合はAIで生成
                    api_key = None
                    
                    # Streamlit Cloud環境でのAPIキー取得
                    if is_streamlit_cloud():
                        try:
                            import os
                            # まず環境変数から直接取得を試行
                            if 'OPENAI_API_KEY' in os.environ:
                                api_key = os.environ['OPENAI_API_KEY']
                                if not api_key or len(api_key) <= 10:
                                    api_key = None
                            else:
                                # 環境変数にない場合はst.secretsから取得を試行
                                if hasattr(st, 'secrets') and st.secrets is not None:
                                    if 'OPENAI_API_KEY' in st.secrets:
                                        api_key = st.secrets['OPENAI_API_KEY']
                                        if not api_key or len(api_key) <= 10:
                                            api_key = None
                        except Exception:
                            api_key = None
                    
                    # ローカル環境でのAPIキー確認
                    elif not is_streamlit_cloud():
                        try:
                            import os
                            from dotenv import load_dotenv
                            load_dotenv()
                            api_key = os.getenv('OPENAI_API_KEY')
                        except Exception:
                            api_key = None
                    
                    if api_key:
                        try:
                            import openai
                            
                            # 古いバージョンのOpenAIライブラリとの互換性を確保
                            try:
                                # 新しいバージョン（1.0.0以降）
                                client = openai.OpenAI(api_key=api_key)
                            except TypeError as e:
                                if "proxies" in str(e):
                                    # 古いバージョン（0.x系）
                                    client = openai.Client(api_key=api_key)
                                else:
                                    raise e
                            
                            # 調査要件に基づいてペルソナを生成
                            prompt = f"""
                            以下の調査要件に基づいて、{persona_count}人の仮想ペルソナを生成してください。
                            
                            調査要件:
                            - 商品カテゴリ: {st.session_state.survey_requirements['product_category']}
                            - ターゲット年齢層: {st.session_state.survey_requirements['target_age_range']}
                            - ターゲット性別: {st.session_state.survey_requirements['target_gender']}
                            - 調査目的: {st.session_state.survey_requirements['survey_purpose']}
                            - 追加要件: {st.session_state.survey_requirements['additional_requirements']}
                            
                            各ペルソナは以下の形式で出力してください（JSON形式）:
                            {{
                                "id": "persona_1",
                                "name": "姓名",
                                "age": 年齢,
                                "gender": "性別",
                                "occupation": "職業",
                                "household_composition": "世帯構成",
                                "income_level": "所得レベル",
                                "lifestyle": "ライフスタイル",
                                "shopping_behavior": "購買行動",
                                "personality": "性格・特徴",
                                "hobbies": "趣味・嗜好",
                                "background_story": "詳細な背景ストーリー"
                            }}
                            
                            各ペルソナの間に空行を入れてください。年齢、職業、ライフスタイルは多様にしてください。
                            """
                            
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=2000
                            )
                            
                            # 応答を解析してペルソナを生成
                            ai_response = response.choices[0].message.content
                            personas = []
                            
                            # 応答からペルソナ情報を抽出（簡易的な処理）
                            lines = ai_response.split('\n')
                            current_persona = {}
                            
                            for line in lines:
                                line = line.strip()
                                if line.startswith('"id"'):
                                    if current_persona:
                                        personas.append(current_persona)
                                    current_persona = {}
                                
                                if ':' in line and '"' in line:
                                    try:
                                        key, value = line.split(':', 1)
                                        key = key.strip().strip('"')
                                        value = value.strip().strip(',').strip('"')
                                        current_persona[key] = value
                                    except:
                                        continue
                            
                            if current_persona:
                                personas.append(current_persona)
                            
                            # 生成されたペルソナが不足している場合はサンプルで補完
                            while len(personas) < persona_count:
                                i = len(personas)
                                personas.append({
                                    "id": f"persona_{i+1}",
                                    "name": f"サンプルペルソナ{i+1}",
                                    "age": 25 + (i * 5),
                                    "gender": "女性" if i % 2 == 0 else "男性",
                                    "occupation": ["会社員", "フリーランス", "主婦", "学生", "公務員"][i % 5],
                                    "household_composition": ["一人暮らし", "夫婦", "家族と同居", "ルームシェア"][i % 4],
                                    "income_level": ["200-300万円", "300-500万円", "500-800万円", "800万円以上"][i % 4],
                                    "lifestyle": ["アクティブ", "マイペース", "規則的", "自由奔放"][i % 4],
                                    "shopping_behavior": ["月1回程度", "週1回程度", "必要に応じて", "頻繁に"][i % 4],
                                    "personality": ["慎重派", "冒険的", "実用的", "トレンド重視"][i % 4],
                                    "hobbies": ["読書", "スポーツ", "料理", "旅行", "ゲーム"][i % 5],
                                    "background_story": f"これは{persona_count}番目のペルソナです。詳細な背景情報がここに表示されます。"
                                })
                            
                        except Exception as e:
                            st.error(f"AIペルソナ生成でエラーが発生しました: {str(e)}")
                            # エラーの場合はサンプルペルソナを生成
                            personas = []
                            for i in range(persona_count):
                                personas.append({
                                    "id": f"persona_{i+1}",
                                    "name": f"サンプルペルソナ{i+1}",
                                    "age": 25 + (i * 5),
                                    "gender": "女性" if i % 2 == 0 else "男性",
                                    "occupation": ["会社員", "フリーランス", "主婦", "学生", "公務員"][i % 5],
                                    "household_composition": ["一人暮らし", "夫婦", "家族と同居", "ルームシェア"][i % 4],
                                    "income_level": ["200-300万円", "300-500万円", "500-800万円", "800万円以上"][i % 4],
                                    "lifestyle": ["アクティブ", "マイペース", "規則的", "自由奔放"][i % 4],
                                    "shopping_behavior": ["月1回程度", "週1回程度", "必要に応じて", "頻繁に"][i % 4],
                                    "personality": ["慎重派", "冒険的", "実用的", "トレンド重視"][i % 4],
                                    "hobbies": ["読書", "スポーツ", "料理", "旅行", "ゲーム"][i % 5],
                                    "background_story": f"これは{persona_count}番目のペルソナです。詳細な背景情報がここに表示されます。"
                                })
                    else:
                        # APIキーが設定されていない場合はサンプルペルソナを生成
                        st.info("OpenAI APIキーが設定されていないため、サンプルペルソナを生成します。")
                        personas = []
                        for i in range(persona_count):
                            personas.append({
                                "id": f"persona_{i+1}",
                                "name": f"サンプルペルソナ{i+1}",
                                "age": 25 + (i * 5),
                                "gender": "女性" if i % 2 == 0 else "男性",
                                "occupation": ["会社員", "フリーランス", "主婦", "学生", "公務員"][i % 5],
                                "household_composition": ["一人暮らし", "夫婦", "家族と同居", "ルームシェア"][i % 4],
                                "income_level": ["200-300万円", "300-500万円", "500-800万円", "800万円以上"][i % 4],
                                "lifestyle": ["アクティブ", "マイペース", "規則的", "自由奔放"][i % 4],
                                "shopping_behavior": ["月1回程度", "週1回程度", "必要に応じて", "頻繁に"][i % 4],
                                "personality": ["慎重派", "冒険的", "実用的", "トレンド重視"][i % 4],
                                "hobbies": ["読書", "スポーツ", "料理", "旅行", "ゲーム"][i % 5],
                                "background_story": f"これは{persona_count}番目のペルソナです。詳細な背景情報がここに表示されます。"
                            })
                    
                    st.session_state.personas = personas
                    st.success(f"{len(personas)}人のペルソナが生成されました！")
    
    # 生成されたペルソナの表示
    if st.session_state.personas:
        st.subheader("👥 生成されたペルソナ")
        
        for i, persona in enumerate(st.session_state.personas):
            with st.expander(f"👤 {persona['name']} ({persona['age']}歳, {persona['gender']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**職業:** {persona.get('occupation', '未設定')}")
                    st.write(f"**世帯構成:** {persona.get('household_composition', '未設定')}")
                    st.write(f"**所得レベル:** {persona.get('income_level', '未設定')}")
                    st.write(f"**ライフスタイル:** {persona.get('lifestyle', '未設定')}")
                with col2:
                    st.write(f"**購買行動:** {persona.get('shopping_behavior', '未設定')}")
                    st.write(f"**性格・特徴:** {persona.get('personality', '未設定')}")
                    st.write(f"**趣味・嗜好:** {persona.get('hobbies', '未設定')}")
                
                st.write("**背景ストーリー:**")
                st.write(persona.get('background_story', '詳細な背景情報がここに表示されます。'))
        
        # 次のステップへ
        if st.button("インタビューを開始", type="primary"):
            st.session_state.current_step = 'interview'
            st.rerun()

# ステップ3: インタビュー実施
elif st.session_state.current_step == 'interview':
    st.markdown('<h2 class="section-header">💬 インタビュー実施</h2>', unsafe_allow_html=True)
    
    if not st.session_state.personas:
        st.error("先にペルソナを生成してください。")
        if st.button("ペルソナ生成に戻る"):
            st.session_state.current_step = 'personas'
            st.rerun()
    else:
        # タブでインタビュー方法を選択
        tab1, tab2 = st.tabs(["🎭 1対1チャットインタビュー", "📊 定量調査インタビュー"])
        
        with tab1:
            st.subheader("🎭 1対1チャットインタビュー")
            
            # ペルソナ選択
            if not st.session_state.current_session:
                st.write("インタビューするペルソナを選択してください：")
                persona_options = ["ペルソナを選択してください"] + [f"{p['name']} ({p['age']}歳, {p['gender']})" for p in st.session_state.personas]
                selected_persona_idx = st.selectbox("ペルソナを選択", range(-1, len(st.session_state.personas)), format_func=lambda x: persona_options[x+1] if x >= 0 else persona_options[0])
                
                if selected_persona_idx >= 0 and st.button("インタビュー開始", type="primary"):
                    st.session_state.current_session = selected_persona_idx
                    st.session_state.chat_messages = []
                    st.session_state.input_key = 0  # 入力キーをリセット
                    st.success(f"インタビューを開始しました！{st.session_state.personas[selected_persona_idx]['name']}とのチャットが開始されます。")
                    st.rerun()
            else:
                # チャットインターフェース
                selected_persona = st.session_state.personas[st.session_state.current_session]
                st.info(f"🎭 {selected_persona['name']} ({selected_persona['age']}歳, {selected_persona['gender']}) とのインタビュー中")
                
                # チャット履歴の表示
                chat_container = st.container()
                with chat_container:
                    for message in st.session_state.chat_messages:
                        if message['role'] == 'user':
                            st.markdown(f'<div class="chat-message user-message">👤 **あなた:** {message["content"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message assistant-message">🎭 **{selected_persona["name"]}:** {message["content"]}</div>', unsafe_allow_html=True)
                
                # 入力フィールドのクリア処理
                if st.session_state.clear_input:
                    st.session_state.input_key += 1
                    st.session_state.clear_input = False
                
                # メッセージ入力
                user_message = st.text_input("メッセージを入力してください", key=f"chat_input_{st.session_state.input_key}")
                
                if user_message:
                    # ユーザーメッセージを追加
                    st.session_state.chat_messages.append({"role": "user", "content": user_message})
                    
                    # ペルソナの応答を生成
                    with st.spinner("ペルソナが応答を考え中..."):
                        # GPT APIキーが設定されている場合はAIで生成
                        api_key = None
                        
                        # Streamlit Cloud環境でのAPIキー取得
                        if is_streamlit_cloud():
                            try:
                                import os
                                if 'OPENAI_API_KEY' in os.environ:
                                    api_key = os.environ['OPENAI_API_KEY']
                                    if not api_key or len(api_key) <= 10:
                                        api_key = None
                                else:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                            if not api_key or len(api_key) <= 10:
                                                api_key = None
                            except Exception:
                                api_key = None
                        
                        # ローカル環境でのAPIキー確認
                        elif not is_streamlit_cloud():
                            try:
                                import os
                                from dotenv import load_dotenv
                                load_dotenv()
                                api_key = os.getenv('OPENAI_API_KEY')
                            except Exception:
                                api_key = None
                        
                        if api_key:
                            try:
                                import openai
                                
                                # 古いバージョンのOpenAIライブラリとの互換性を確保
                                try:
                                    client = openai.OpenAI(api_key=api_key)
                                except TypeError as e:
                                    if "proxies" in str(e):
                                        client = openai.Client(api_key=api_key)
                                    else:
                                        raise e
                                
                                # ペルソナの背景情報を含むプロンプト
                                prompt = f"""
                                あなたは{selected_persona['name']}という{selected_persona['age']}歳の{selected_persona['gender']}です。
                                以下の背景情報に基づいて、自然で一貫性のある応答をしてください。
                                
                                背景情報:
                                - 職業: {selected_persona.get('occupation', '未設定')}
                                - 世帯構成: {selected_persona.get('household_composition', '未設定')}
                                - 所得レベル: {selected_persona.get('income_level', '未設定')}
                                - ライフスタイル: {selected_persona.get('lifestyle', '未設定')}
                                - 購買行動: {selected_persona.get('shopping_behavior', '未設定')}
                                - 性格・特徴: {selected_persona.get('personality', '未設定')}
                                - 趣味・嗜好: {selected_persona.get('hobbies', '未設定')}
                                - 背景ストーリー: {selected_persona.get('background_story', '未設定')}
                                
                                ユーザーの質問: {user_message}
                                
                                このペルソナの視点から、自然で親しみやすい口調で応答してください。
                                """
                                
                                response = client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[{"role": "user", "content": prompt}],
                                    max_tokens=500
                                )
                                
                                persona_response = response.choices[0].message.content
                                
                            except Exception as e:
                                st.error(f"AI応答生成でエラーが発生しました: {str(e)}")
                                persona_response = f"申し訳ございません。現在、応答を生成できません。エラー: {str(e)}"
                        else:
                            # APIキーが設定されていない場合はサンプル応答
                            sample_responses = [
                                "そうですね、とても興味深い質問ですね。個人的には...",
                                "なるほど、確かにその通りだと思います。私の経験では...",
                                "面白い視点ですね。私の立場から考えると...",
                                "そういう考え方もありますね。私としては...",
                                "確かに、その通りかもしれません。私の場合は..."
                            ]
                            import random
                            persona_response = random.choice(sample_responses)
                        
                        # ペルソナの応答を追加
                        st.session_state.chat_messages.append({"role": "assistant", "content": persona_response})
                        
                        # 成功メッセージを表示
                        st.success("応答が生成されました！")
                        
                        # 入力フィールドをクリアするためにセッション状態にフラグを設定
                        st.session_state.clear_input = True
                        
                        # チャット履歴を更新
                        st.rerun()
                
                # インタビュー終了
                if st.button("インタビュー終了"):
                    st.session_state.current_session = None
                    st.rerun()
        
        with tab2:
            st.subheader("📊 定量調査インタビュー")
            
            # 質問タイプ選択
            question_type = st.selectbox(
                "質問タイプを選択",
                ["選択式（ラジオボタン）", "選択式（チェックボックス）", "自由記述"]
            )
            
            # 質問入力
            question_text = st.text_input("質問内容を入力してください", placeholder="例：この商品を購入する際に最も重視する点は何ですか？")
            
            if question_type == "選択式（ラジオボタン）":
                options_input = st.text_area("選択肢を入力（1行に1つ）", placeholder="価格\n品質\nデザイン\nブランド\nその他")
                
                if st.button("定量調査を実行", type="primary") and question_text and options_input:
                    options = [opt.strip() for opt in options_input.split('\n') if opt.strip()]
                    
                    if len(options) >= 2:
                        # 全ペルソナに同じ質問を投げかける
                        results = []
                        
                        for persona in st.session_state.personas:
                            # GPT APIキーが設定されている場合はAIで生成
                            api_key = None
                            
                            if is_streamlit_cloud():
                                try:
                                    import os
                                    if 'OPENAI_API_KEY' in os.environ:
                                        api_key = os.environ['OPENAI_API_KEY']
                                        if not api_key or len(api_key) <= 10:
                                            api_key = None
                                    else:
                                        if hasattr(st, 'secrets') and st.secrets is not None:
                                            if 'OPENAI_API_KEY' in st.secrets:
                                                api_key = st.secrets['OPENAI_API_KEY']
                                                if not api_key or len(api_key) <= 10:
                                                    api_key = None
                                except Exception:
                                    api_key = None
                            
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception:
                                    api_key = None
                            
                            if api_key:
                                try:
                                    import openai
                                    
                                    try:
                                        client = openai.OpenAI(api_key=api_key)
                                    except TypeError as e:
                                        if "proxies" in str(e):
                                            client = openai.Client(api_key=api_key)
                                        else:
                                            raise e
                                    
                                    prompt = f"""
                                    あなたは{persona['name']}という{persona['age']}歳の{persona['gender']}です。
                                    以下の背景情報に基づいて、与えられた選択肢から最も適切な回答を1つ選んでください。
                                    
                                    背景情報:
                                    - 職業: {persona.get('occupation', '未設定')}
                                    - 世帯構成: {persona.get('household_composition', '未設定')}
                                    - 所得レベル: {persona.get('income_level', '未設定')}
                                    - ライフスタイル: {persona.get('lifestyle', '未設定')}
                                    - 購買行動: {persona.get('shopping_behavior', '未設定')}
                                    - 性格・特徴: {persona.get('personality', '未設定')}
                                    - 趣味・嗜好: {persona.get('hobbies', '未設定')}
                                    
                                    質問: {question_text}
                                    選択肢: {', '.join(options)}
                                    
                                    このペルソナの視点から、最も適切な選択肢を1つ選んでください。
                                    回答は選択肢の文字列のみでお願いします。
                                    """
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=100
                                    )
                                    
                                    answer = response.choices[0].message.content.strip()
                                    # 選択肢に含まれていない場合は最初の選択肢を使用
                                    if answer not in options:
                                        answer = options[0]
                                    
                                except Exception as e:
                                    st.error(f"AI応答生成でエラーが発生しました: {str(e)}")
                                    import random
                                    answer = random.choice(options)
                            else:
                                # APIキーが設定されていない場合はランダム選択
                                import random
                                answer = random.choice(options)
                            
                            results.append({
                                "persona": persona['name'],
                                "answer": answer
                            })
                        
                        # 結果を集計
                        answer_counts = {}
                        for result in results:
                            answer = result['answer']
                            answer_counts[answer] = answer_counts.get(answer, 0) + 1
                        
                        # 結果表示
                        st.subheader("📊 調査結果")
                        
                        # 表形式で表示
                        st.write("**個別回答:**")
                        for result in results:
                            st.write(f"- {result['persona']}: {result['answer']}")
                        
                        # グラフ表示
                        if answer_counts:
                            st.write("**集計結果:**")
                            fig = px.bar(
                                x=list(answer_counts.keys()),
                                y=list(answer_counts.values()),
                                title="回答の分布",
                                labels={'x': '選択肢', 'y': '回答数'}
                            )
                            st.plotly_chart(fig)
                        
                        # 結果をセッション状態に保存
                        st.session_state.fixed_interviews.append({
                            "question": question_text,
                            "type": question_type,
                            "options": options,
                            "results": results,
                            "timestamp": datetime.now()
                        })
                        
                        st.success("定量調査が完了しました！")
                    else:
                        st.error("選択肢は2つ以上入力してください。")
                else:
                    st.warning("質問内容と選択肢を入力してください。")
            
            elif question_type == "選択式（チェックボックス）":
                options_input = st.text_area("選択肢を入力（1行に1つ）", placeholder="価格\n品質\nデザイン\nブランド\nその他")
                
                if st.button("定量調査を実行", type="primary") and question_text and options_input:
                    options = [opt.strip() for opt in options_input.split('\n') if opt.strip()]
                    
                    if len(options) >= 2:
                        # 全ペルソナに同じ質問を投げかける
                        results = []
                        
                        for persona in st.session_state.personas:
                            # GPT APIキーが設定されている場合はAIで生成
                            api_key = None
                            
                            if is_streamlit_cloud():
                                try:
                                    import os
                                    if 'OPENAI_API_KEY' in os.environ:
                                        api_key = os.environ['OPENAI_API_KEY']
                                        if not api_key or len(api_key) <= 10:
                                            api_key = None
                                    else:
                                        if hasattr(st, 'secrets') and st.secrets is not None:
                                            if 'OPENAI_API_KEY' in st.secrets:
                                                api_key = st.secrets['OPENAI_API_KEY']
                                                if not api_key or len(api_key) <= 10:
                                                    api_key = None
                                except Exception:
                                    api_key = None
                            
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception:
                                    api_key = None
                            
                            if api_key:
                                try:
                                    import openai
                                    
                                    try:
                                        client = openai.OpenAI(api_key=api_key)
                                    except TypeError as e:
                                        if "proxies" in str(e):
                                            client = openai.Client(api_key=api_key)
                                        else:
                                            raise e
                                    
                                    prompt = f"""
                                    あなたは{persona['name']}という{persona['age']}歳の{persona['gender']}です。
                                    以下の背景情報に基づいて、与えられた選択肢から適切な回答を複数選んでください。
                                    
                                    背景情報:
                                    - 職業: {persona.get('occupation', '未設定')}
                                    - 世帯構成: {persona.get('household_composition', '未設定')}
                                    - 所得レベル: {persona.get('income_level', '未設定')}
                                    - ライフスタイル: {persona.get('lifestyle', '未設定')}
                                    - 購買行動: {persona.get('shopping_behavior', '未設定')}
                                    - 性格・特徴: {persona.get('personality', '未設定')}
                                    - 趣味・嗜好: {persona.get('hobbies', '未設定')}
                                    
                                    質問: {question_text}
                                    選択肢: {', '.join(options)}
                                    
                                    このペルソナの視点から、適切な選択肢を複数選んでください。
                                    回答は選択肢の文字列をカンマ区切りでお願いします。
                                    """
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=200
                                    )
                                    
                                    answer_text = response.choices[0].message.content.strip()
                                    # カンマ区切りで分割
                                    answers = [ans.strip() for ans in answer_text.split(',') if ans.strip() in options]
                                    if not answers:
                                        answers = [options[0]]
                                    
                                except Exception as e:
                                    st.error(f"AI応答生成でエラーが発生しました: {str(e)}")
                                    import random
                                    # ランダムに1-3個選択
                                    num_choices = random.randint(1, min(3, len(options)))
                                    answers = random.sample(options, num_choices)
                            else:
                                # APIキーが設定されていない場合はランダム選択
                                import random
                                num_choices = random.randint(1, min(3, len(options)))
                                answers = random.sample(options, num_choices)
                            
                            results.append({
                                "persona": persona['name'],
                                "answers": answers
                            })
                        
                        # 結果を集計
                        answer_counts = {}
                        for result in results:
                            for answer in result['answers']:
                                answer_counts[answer] = answer_counts.get(answer, 0) + 1
                        
                        # 結果表示
                        st.subheader("📊 調査結果")
                        
                        # 表形式で表示
                        st.write("**個別回答:**")
                        for result in results:
                            st.write(f"- {result['persona']}: {', '.join(result['answers'])}")
                        
                        # グラフ表示
                        if answer_counts:
                            st.write("**集計結果:**")
                            fig = px.bar(
                                x=list(answer_counts.keys()),
                                y=list(answer_counts.values()),
                                title="回答の分布",
                                labels={'x': '選択肢', 'y': '回答数'}
                            )
                            st.plotly_chart(fig)
                        
                        # 結果をセッション状態に保存
                        st.session_state.fixed_interviews.append({
                            "question": question_text,
                            "type": question_type,
                            "options": options,
                            "results": results,
                            "timestamp": datetime.now()
                        })
                        
                        st.success("定量調査が完了しました！")
                    else:
                        st.error("選択肢は2つ以上入力してください。")
                else:
                    st.warning("質問内容と選択肢を入力してください。")
            
            else:  # 自由記述
                if st.button("定量調査を実行", type="primary") and question_text:
                    # 全ペルソナに同じ質問を投げかける
                    results = []
                    
                    for persona in st.session_state.personas:
                        # GPT APIキーが設定されている場合はAIで生成
                        api_key = None
                        
                        if is_streamlit_cloud():
                            try:
                                import os
                                if 'OPENAI_API_KEY' in os.environ:
                                    api_key = os.environ['OPENAI_API_KEY']
                                    if not api_key or len(api_key) <= 10:
                                        api_key = None
                                else:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                            if not api_key or len(api_key) <= 10:
                                                api_key = None
                            except Exception:
                                api_key = None
                        
                        elif not is_streamlit_cloud():
                            try:
                                import os
                                from dotenv import load_dotenv
                                load_dotenv()
                                api_key = os.getenv('OPENAI_API_KEY')
                            except Exception:
                                api_key = None
                        
                        if api_key:
                            try:
                                import openai
                                
                                try:
                                    client = openai.OpenAI(api_key=api_key)
                                except TypeError as e:
                                    if "proxies" in str(e):
                                        client = openai.Client(api_key=api_key)
                                    else:
                                        raise e
                                
                                prompt = f"""
                                あなたは{persona['name']}という{persona['age']}歳の{persona['gender']}です。
                                以下の背景情報に基づいて、自然で一貫性のある回答をしてください。
                                
                                背景情報:
                                - 職業: {persona.get('occupation', '未設定')}
                                - 世帯構成: {persona.get('household_composition', '未設定')}
                                - 所得レベル: {persona.get('income_level', '未設定')}
                                - ライフスタイル: {persona.get('lifestyle', '未設定')}
                                - 購買行動: {persona.get('shopping_behavior', '未設定')}
                                - 性格・特徴: {persona.get('personality', '未設定')}
                                - 趣味・嗜好: {persona.get('hobbies', '未設定')}
                                
                                質問: {question_text}
                                
                                このペルソナの視点から、自然で親しみやすい口調で回答してください。
                                回答は100文字程度でお願いします。
                                """
                                
                                response = client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[{"role": "user", "content": prompt}],
                                    max_tokens=200
                                )
                                
                                answer = response.choices[0].message.content.strip()
                                
                            except Exception as e:
                                st.error(f"AI応答生成でエラーが発生しました: {str(e)}")
                                answer = f"申し訳ございません。現在、回答を生成できません。エラー: {str(e)}"
                        else:
                            # APIキーが設定されていない場合はサンプル回答
                            sample_answers = [
                                "個人的には、とても興味深い質問だと思います。",
                                "そうですね、確かにその通りだと思います。",
                                "面白い視点ですね。私の立場から考えると...",
                                "そういう考え方もありますね。私としては...",
                                "確かに、その通りかもしれません。"
                            ]
                            import random
                            answer = random.choice(sample_answers)
                        
                        results.append({
                            "persona": persona['name'],
                            "answer": answer
                        })
                    
                    # 結果表示
                    st.subheader("📊 調査結果")
                    
                    # 表形式で表示
                    st.write("**個別回答:**")
                    for result in results:
                        st.write(f"- **{result['persona']}:** {result['answer']}")
                    
                    # 結果をセッション状態に保存
                    st.session_state.fixed_interviews.append({
                        "question": question_text,
                        "type": question_type,
                        "options": None,
                        "results": results,
                        "timestamp": datetime.now()
                    })
                    
                    st.success("定量調査が完了しました！")
                else:
                    st.warning("質問内容を入力してください。")
        
        # 次のステップへ
        if st.button("結果サマリーへ", type="primary"):
            st.session_state.current_step = 'summary'
            st.rerun()

# ステップ4: 結果サマリー
elif st.session_state.current_step == 'summary':
    st.markdown('<h2 class="section-header">📋 結果サマリー</h2>', unsafe_allow_html=True)
    
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
    
    # 生成されたペルソナの概要
    if st.session_state.personas:
        st.subheader("👥 生成されたペルソナ概要")
        st.write(f"**総ペルソナ数:** {len(st.session_state.personas)}人")
        
        # 年齢分布
        ages = []
        for p in st.session_state.personas:
            try:
                age = p.get('age')
                if age and str(age).isdigit():
                    ages.append(int(age))
            except (ValueError, TypeError):
                continue
        
        if ages:
            st.write(f"**年齢範囲:** {min(ages)}歳 - {max(ages)}歳")
            st.write(f"**平均年齢:** {sum(ages) // len(ages)}歳")
        
        # 性別分布
        gender_counts = {}
        for p in st.session_state.personas:
            try:
                gender = p.get('gender', '未設定')
                if gender and str(gender).strip():
                    gender_counts[gender] = gender_counts.get(gender, 0) + 1
            except (ValueError, TypeError):
                continue
        
        if gender_counts:
            st.write("**性別分布:**")
            for gender, count in gender_counts.items():
                st.write(f"- {gender}: {count}人")
        
        # 職業分布
        occupation_counts = {}
        for p in st.session_state.personas:
            try:
                occupation = p.get('occupation', '未設定')
                if occupation and str(occupation).strip():
                    occupation_counts[occupation] = occupation_counts.get(occupation, 0) + 1
            except (ValueError, TypeError):
                continue
        
        if occupation_counts:
            st.write("**職業分布:**")
            for occupation, count in occupation_counts.items():
                st.write(f"- {occupation}: {count}人")
    
    # 実施されたインタビューの結果
    if st.session_state.fixed_interviews:
        st.subheader("📊 実施された定量調査")
        
        for i, interview in enumerate(st.session_state.fixed_interviews):
            with st.expander(f"調査{i+1}: {interview['question']} ({interview['type']})"):
                st.write(f"**実施日時:** {interview['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**質問タイプ:** {interview['type']}")
                
                if interview['options']:
                    st.write(f"**選択肢:** {', '.join(interview['options'])}")
                
                st.write("**回答結果:**")
                for result in interview['results']:
                    if 'answers' in result:  # チェックボックス形式
                        st.write(f"- {result['persona']}: {', '.join(result['answers'])}")
                    else:  # ラジオボタンまたは自由記述
                        st.write(f"- {result['persona']}: {result['answer']}")
                
                # 集計結果の表示（選択式の場合）
                if interview['options']:
                    if 'answers' in interview['results'][0]:  # チェックボックス形式
                        answer_counts = {}
                        for result in interview['results']:
                            for answer in result['answers']:
                                answer_counts[answer] = answer_counts.get(answer, 0) + 1
                    else:  # ラジオボタン形式
                        answer_counts = {}
                        for result in interview['results']:
                            answer = result['answer']
                            answer_counts[answer] = answer_counts.get(answer, 0) + 1
                    
                    if answer_counts:
                        st.write("**集計結果:**")
                        fig = px.bar(
                            x=list(answer_counts.keys()),
                            y=list(answer_counts.values()),
                            title=f"調査{i+1}の回答分布",
                            labels={'x': '選択肢', 'y': '回答数'}
                        )
                        st.plotly_chart(fig)
    
    # チャットインタビューの履歴
    if st.session_state.chat_messages:
        st.subheader("💬 チャットインタビューの履歴")
        
        # 最新のチャットセッションを表示
        if st.session_state.current_session is not None:
            selected_persona = st.session_state.personas[st.session_state.current_session]
            st.write(f"**インタビュー対象:** {selected_persona['name']} ({selected_persona['age']}歳, {selected_persona['gender']})")
            
            with st.expander("会話履歴を表示", expanded=False):
                for message in st.session_state.chat_messages:
                    if message['role'] == 'user':
                        st.markdown(f'<div class="chat-message user-message">👤 **あなた:** {message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message">🎭 **{selected_persona["name"]}:** {message["content"]}</div>', unsafe_allow_html=True)
    
    # サマリーの生成
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("AIサマリーを生成", type="primary", use_container_width=True):
            if st.session_state.fixed_interviews or st.session_state.chat_messages:
                with st.spinner("AIサマリーを生成中..."):
                    # GPT APIキーが設定されている場合はAIで生成
                    api_key = None
                    
                    # Streamlit Cloud環境でのAPIキー取得
                    if is_streamlit_cloud():
                        try:
                            import os
                            if 'OPENAI_API_KEY' in os.environ:
                                api_key = os.environ['OPENAI_API_KEY']
                                if not api_key or len(api_key) <= 10:
                                    api_key = None
                            else:
                                if hasattr(st, 'secrets') and st.secrets is not None:
                                    if 'OPENAI_API_KEY' in st.secrets:
                                        api_key = st.secrets['OPENAI_API_KEY']
                                        if not api_key or len(api_key) <= 10:
                                            api_key = None
                        except Exception:
                            api_key = None
                    
                    # ローカル環境でのAPIキー確認
                    elif not is_streamlit_cloud():
                        try:
                            import os
                            from dotenv import load_dotenv
                            load_dotenv()
                            api_key = os.getenv('OPENAI_API_KEY')
                        except Exception:
                            api_key = None
                    
                    if api_key:
                        try:
                            import openai
                            
                            try:
                                client = openai.OpenAI(api_key=api_key)
                            except TypeError as e:
                                if "proxies" in str(e):
                                    client = openai.Client(api_key=api_key)
                                else:
                                    raise e
                            
                            # サマリー生成のプロンプト
                            try:
                                summary_prompt = f"""
                                以下の調査結果を分析して、ビジネスに活用できる洞察を含むサマリーレポートを作成してください。
                                
                                調査要件:
                                - 商品カテゴリ: {st.session_state.survey_requirements.get('product_category', '未設定')}
                                - ターゲット年齢層: {st.session_state.survey_requirements.get('target_age_range', '未設定')}
                                - ターゲット性別: {st.session_state.survey_requirements.get('target_gender', '未設定')}
                                - 調査目的: {st.session_state.survey_requirements.get('survey_purpose', '未設定')}
                                - 追加要件: {st.session_state.survey_requirements.get('additional_requirements', '未設定')}
                                
                                生成されたペルソナ数: {len(st.session_state.personas)}人
                                
                                実施された定量調査数: {len(st.session_state.fixed_interviews)}件
                                
                                以下の形式でサマリーを作成してください：
                                
                                ## 調査概要
                                [調査の目的と対象の概要]
                                
                                ## 主要な発見
                                [最も重要な発見事項を3-5点]
                                
                                ## ターゲット分析
                                [ペルソナの特徴と傾向]
                                
                                ## ビジネス洞察
                                [商品開発やマーケティングへの示唆]
                                
                                ## 今後のアクション
                                [推奨される次のステップ]
                                
                                サマリーは日本語で、実用的で分かりやすい内容にしてください。
                                """
                            except Exception as e:
                                st.error(f"サマリープロンプトの生成でエラーが発生しました: {str(e)}")
                                summary_prompt = "調査結果のサマリーを作成してください。"
                            
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": summary_prompt}],
                                max_tokens=1000
                            )
                            
                            ai_summary = response.choices[0].message.content
                            st.session_state.summary = ai_summary
                            
                            st.success("AIサマリーが生成されました！")
                            
                        except Exception as e:
                            st.error(f"AIサマリー生成でエラーが発生しました: {str(e)}")
                            st.session_state.summary = "AIサマリーの生成に失敗しました。"
                    else:
                        st.warning("OpenAI APIキーが設定されていないため、AIサマリーを生成できません。")
                        st.session_state.summary = "APIキーが設定されていないため、AIサマリーを生成できません。"
        
        # サマリーの表示
        if st.session_state.summary:
            st.subheader("🤖 AI生成サマリー")
            st.markdown(st.session_state.summary)
    
    # 最初からやり直す
    if st.button("最初からやり直す", type="primary"):
        # セッション状態をリセット
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# フッター
st.divider()
st.caption("© 2024 仮想インタビューシステム v2.0.0")
