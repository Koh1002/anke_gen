import streamlit as st
from typing import Dict, Any, List
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
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = None

# API設定 - Streamlit Cloud環境では直接処理
def is_streamlit_cloud():
    """Streamlit Cloud環境かどうかを判定"""
    try:
        # Streamlit Cloud環境の判定
        import os
        
        # デバッグ情報
        st.caption(f"環境変数一覧: {list(os.environ.keys())}")
        
        # 最も確実な判定：OPENAI_API_KEY環境変数の存在確認
        if 'OPENAI_API_KEY' in os.environ:
            st.caption("OPENAI_API_KEY環境変数でStreamlit Cloudと判定")
            return True
        
        # 環境変数で判定（Streamlit Cloud特有の環境変数）
        if 'STREAMLIT_CLOUD_ENVIRONMENT' in os.environ:
            st.caption("STREAMLIT_CLOUD_ENVIRONMENT環境変数で判定")
            return True
        
        # より確実な判定：st.secretsの存在確認
        if hasattr(st, 'secrets') and st.secrets is not None:
            st.caption("st.secretsが存在します")
            # secretsが存在し、かつ何らかの値が設定されている場合はStreamlit Cloudと判断
            try:
                # secretsの内容を確認（空でない場合）
                if hasattr(st.secrets, '_secrets') and len(st.secrets._secrets) > 0:
                    st.caption(f"st.secrets._secretsの長さ: {len(st.secrets._secrets)}")
                    return True
                # 直接アクセス可能な場合
                if hasattr(st.secrets, 'get') and callable(getattr(st.secrets, 'get')):
                    st.caption("st.secrets.getメソッドが利用可能")
                    return True
            except Exception as e:
                st.caption(f"st.secretsの詳細確認でエラー: {str(e)}")
                pass
        
        # ホスト名で判定（最後の手段）
        import socket
        hostname = socket.gethostname()
        st.caption(f"ホスト名: {hostname}")
        if 'streamlit' in hostname.lower() or 'cloud' in hostname.lower():
            st.caption("ホスト名でStreamlit Cloudと判定")
            return True
        
        st.caption("ローカル環境と判定")
        # ローカル環境と判断
        return False
    except Exception as e:
        st.caption(f"環境判定でエラー: {str(e)}")
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
    
    # デバッグ情報
    st.caption(f"環境判定: {'Streamlit Cloud' if is_streamlit_cloud() else 'ローカル'}")
    
    if is_streamlit_cloud():
        try:
            # Streamlit Cloud環境でのAPIキー確認
            if hasattr(st, 'secrets') and st.secrets is not None:
                if 'OPENAI_API_KEY' in st.secrets:
                    st.success("✅ OpenAI APIキーが設定されています")
                    # APIキーの一部を表示（セキュリティのため最初の4文字のみ）
                    api_key = st.secrets['OPENAI_API_KEY']
                    if api_key:
                        st.caption(f"APIキー: {api_key[:4]}...{api_key[-4:]}")
                else:
                    st.warning("⚠️ OpenAI APIキーが設定されていません")
                    st.info("Streamlit Cloudのsecretsで設定してください")
            else:
                st.error("❌ st.secretsが利用できません")
        except Exception as e:
            st.warning(f"⚠️ API設定の確認に失敗しました: {str(e)}")
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
                    
                    # デバッグ情報を収集
                    debug_info = {
                        "environment": "Streamlit Cloud" if is_streamlit_cloud() else "ローカル",
                        "env_vars": {},
                        "secrets_info": {},
                        "api_key_status": {},
                        "ai_generation_status": {}
                    }
                    
                    # 環境変数の詳細確認
                    import os
                    debug_info["env_vars"] = {
                        "OPENAI_API_KEY_exists": 'OPENAI_API_KEY' in os.environ,
                        "OPENAI_API_KEY_length": len(os.environ.get('OPENAI_API_KEY', '')) if 'OPENAI_API_KEY' in os.environ else 0,
                        "OPENAI_API_KEY_preview": os.environ.get('OPENAI_API_KEY', '')[:4] + "..." + os.environ.get('OPENAI_API_KEY', '')[-4:] if 'OPENAI_API_KEY' in os.environ and os.environ.get('OPENAI_API_KEY') else "なし"
                    }
                    
                    # st.secretsの詳細確認
                    debug_info["secrets_info"] = {
                        "exists": hasattr(st, 'secrets') and st.secrets is not None,
                        "type": str(type(st.secrets)) if hasattr(st, 'secrets') else "なし",
                        "has_secrets": hasattr(st.secrets, '_secrets') and len(st.secrets._secrets) > 0 if hasattr(st, 'secrets') else False,
                        "secrets_length": len(st.secrets._secrets) if hasattr(st, 'secrets') and hasattr(st.secrets, '_secrets') else 0,
                        "available_keys": list(st.secrets.keys()) if hasattr(st, 'secrets') and hasattr(st.secrets, 'keys') else []
                    }
                    
                    # Streamlit Cloud環境でのAPIキー取得
                    if is_streamlit_cloud():
                        try:
                            # まず環境変数から直接取得を試行
                            if 'OPENAI_API_KEY' in os.environ:
                                api_key = os.environ['OPENAI_API_KEY']
                                if api_key and len(api_key) > 10:
                                    debug_info["api_key_status"] = {
                                        "source": "環境変数",
                                        "status": "成功",
                                        "length": len(api_key),
                                        "preview": api_key[:4] + "..." + api_key[-4:]
                                    }
                                else:
                                    debug_info["api_key_status"] = {
                                        "source": "環境変数",
                                        "status": "失敗",
                                        "reason": "空または短すぎる",
                                        "length": len(api_key) if api_key else 0
                                    }
                                    api_key = None
                            else:
                                # 環境変数にない場合はst.secretsから取得を試行
                                if hasattr(st, 'secrets') and st.secrets is not None:
                                    if 'OPENAI_API_KEY' in st.secrets:
                                        api_key = st.secrets['OPENAI_API_KEY']
                                        if api_key and len(api_key) > 10:
                                            debug_info["api_key_status"] = {
                                                "source": "st.secrets",
                                                "status": "成功",
                                                "length": len(api_key),
                                                "preview": api_key[:4] + "..." + api_key[-4:]
                                            }
                                        else:
                                            debug_info["api_key_status"] = {
                                                "source": "st.secrets",
                                                "status": "失敗",
                                                "reason": "空または短すぎる",
                                                "length": len(api_key) if api_key else 0
                                            }
                                            api_key = None
                                    else:
                                        debug_info["api_key_status"] = {
                                            "source": "st.secrets",
                                            "status": "失敗",
                                            "reason": "OPENAI_API_KEYが設定されていない",
                                            "available_keys": list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else []
                                        }
                                        api_key = None
                                else:
                                    debug_info["api_key_status"] = {
                                        "source": "st.secrets",
                                        "status": "失敗",
                                        "reason": "st.secretsが利用できない"
                                    }
                                    api_key = None
                        except Exception as e:
                            debug_info["api_key_status"] = {
                                "source": "エラー",
                                "status": "失敗",
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                            api_key = None
                    
                    # ローカル環境でのAPIキー確認
                    elif not is_streamlit_cloud():
                        try:
                            from dotenv import load_dotenv
                            load_dotenv()
                            api_key = os.getenv('OPENAI_API_KEY')
                            if api_key:
                                debug_info["api_key_status"] = {
                                    "source": ".envファイル",
                                    "status": "成功",
                                    "length": len(api_key),
                                    "preview": api_key[:4] + "..." + api_key[-4:]
                                }
                            else:
                                debug_info["api_key_status"] = {
                                    "source": ".envファイル",
                                    "status": "失敗",
                                    "reason": "OPENAI_API_KEYが設定されていない"
                                }
                        except Exception as e:
                            debug_info["api_key_status"] = {
                                "source": ".envファイル",
                                "status": "失敗",
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                            api_key = None
                    
                    # AI生成処理の状態を記録
                    if api_key:
                        debug_info["ai_generation_status"] = {
                            "status": "APIキーあり - AI生成可能",
                            "api_key_length": len(api_key),
                            "api_key_preview": api_key[:4] + "..." + api_key[-4:]
                        }
                    else:
                        debug_info["ai_generation_status"] = {
                            "status": "APIキーなし - サンプル生成",
                            "reason": "APIキーが設定されていないため"
                        }
                    
                    # デバッグ情報をセッション状態に保存
                    st.session_state.debug_info = debug_info
                    
                    # デバッグ情報を表示
                    st.markdown("---")
                    st.markdown("### 🔍 デバッグ情報")
                    st.info(f"環境判定結果: {debug_info['environment']}")
                    
                    # 環境変数の詳細確認
                    st.markdown("#### 📋 環境変数の詳細確認")
                    st.info(f"環境変数OPENAI_API_KEYの存在: {debug_info['env_vars']['OPENAI_API_KEY_exists']}")
                    if debug_info['env_vars']['OPENAI_API_KEY_exists']:
                        st.info(f"環境変数のAPIキー長: {debug_info['env_vars']['OPENAI_API_KEY_length']}")
                        if debug_info['env_vars']['OPENAI_API_KEY_preview'] != "なし":
                            st.info(f"環境変数のAPIキー内容: {debug_info['env_vars']['OPENAI_API_KEY_preview']}")
                    
                    # st.secretsの詳細確認
                    st.markdown("#### 🔐 st.secretsの詳細確認")
                    st.info(f"st.secretsの存在: {debug_info['secrets_info']['exists']}")
                    if debug_info['secrets_info']['exists']:
                        st.info(f"st.secretsの型: {debug_info['secrets_info']['type']}")
                        st.info(f"st.secrets._secretsの長さ: {debug_info['secrets_info']['secrets_length']}")
                        if debug_info['secrets_info']['available_keys']:
                            st.info(f"利用可能なsecrets: {debug_info['secrets_info']['available_keys']}")
                    
                    # APIキー取得処理の結果
                    st.markdown("#### 🚀 APIキー取得処理")
                    api_status = debug_info['api_key_status']
                    if api_status['status'] == '成功':
                        st.success(f"{api_status['source']}からAPIキーを取得しました: {api_status['preview']}")
                        st.info(f"APIキーの長さ: {api_status['length']}文字")
                    else:
                        st.warning(f"{api_status['source']}からのAPIキー取得に失敗: {api_status.get('reason', api_status.get('error', '不明'))}")
                    
                    # AI生成処理の状態
                    st.markdown("#### 🤖 AI生成処理の開始判定")
                    ai_status = debug_info['ai_generation_status']
                    if ai_status['status'].startswith('APIキーあり'):
                        st.success(f"最終確認: APIキーが設定されています ({ai_status['api_key_preview']})")
                        st.info(f"APIキーの完全な長さ: {ai_status['api_key_length']}文字")
                    else:
                        st.warning("最終確認: APIキーが設定されていません")
                        st.error(f"⚠️ {ai_status['reason']}のため、サンプルペルソナが生成されます")
                    
                    if api_key:
                        try:
                            st.info("OpenAI APIを使用してペルソナ生成を開始...")
                            import openai
                            client = openai.OpenAI(api_key=api_key)
                            
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
                            
                            st.info("OpenAI APIにリクエストを送信中...")
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=2000
                            )
                            
                            st.success("OpenAI APIからの応答を受信しました！")
                            
                            # 応答を解析してペルソナを生成
                            ai_response = response.choices[0].message.content
                            st.info(f"AI応答の長さ: {len(ai_response)}文字")
                            st.info(f"AI応答の最初の100文字: {ai_response[:100]}...")
                            
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
                            
                            st.info(f"解析されたペルソナ数: {len(personas)}")
                            
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
                            st.error(f"エラーの詳細: {type(e).__name__}")
                            st.error(f"エラーの内容: {str(e)}")
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
                    
                    # デバッグ情報を永続的に表示
                    st.info("✅ デバッグ情報が表示されています。画面遷移後も確認できます。")
    
    # 生成されたペルソナの表示
    if st.session_state.personas:
        # デバッグ情報の表示（セッション状態に保存されている場合）
        if st.session_state.debug_info:
            with st.expander("🔍 デバッグ情報を表示", expanded=False):
                debug_info = st.session_state.debug_info
                st.markdown("### 🔍 デバッグ情報")
                st.info(f"環境判定結果: {debug_info['environment']}")
                
                # 環境変数の詳細確認
                st.markdown("#### 📋 環境変数の詳細確認")
                st.info(f"環境変数OPENAI_API_KEYの存在: {debug_info['env_vars']['OPENAI_API_KEY_exists']}")
                if debug_info['env_vars']['OPENAI_API_KEY_exists']:
                    st.info(f"環境変数のAPIキー長: {debug_info['env_vars']['OPENAI_API_KEY_length']}")
                    if debug_info['env_vars']['OPENAI_API_KEY_preview'] != "なし":
                        st.info(f"環境変数のAPIキー内容: {debug_info['env_vars']['OPENAI_API_KEY_preview']}")
                
                # st.secretsの詳細確認
                st.markdown("#### 🔐 st.secretsの詳細確認")
                st.info(f"st.secretsの存在: {debug_info['secrets_info']['exists']}")
                if debug_info['secrets_info']['exists']:
                    st.info(f"st.secretsの型: {debug_info['secrets_info']['type']}")
                    st.info(f"st.secrets._secretsの長さ: {debug_info['secrets_info']['secrets_length']}")
                    if debug_info['secrets_info']['available_keys']:
                        st.info(f"利用可能なsecrets: {debug_info['secrets_info']['available_keys']}")
                
                # APIキー取得処理の結果
                st.markdown("#### 🚀 APIキー取得処理")
                api_status = debug_info['api_key_status']
                if api_status['status'] == '成功':
                    st.success(f"{api_status['source']}からAPIキーを取得しました: {api_status['preview']}")
                    st.info(f"APIキーの長さ: {api_status['length']}文字")
                else:
                    st.warning(f"{api_status['source']}からのAPIキー取得に失敗: {api_status.get('reason', api_status.get('error', '不明'))}")
                
                # AI生成処理の状態
                st.markdown("#### 🤖 AI生成処理の開始判定")
                ai_status = debug_info['ai_generation_status']
                if ai_status['status'].startswith('APIキーあり'):
                    st.success(f"最終確認: APIキーが設定されています ({ai_status['api_key_preview']})")
                    st.info(f"APIキーの完全な長さ: {ai_status['api_key_length']}文字")
                else:
                    st.warning("最終確認: APIキーが設定されていません")
                    st.error(f"⚠️ {ai_status['reason']}のため、サンプルペルソナが生成されます")
        
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
                    # Streamlit Cloud環境用のセッション作成
                    session = {
                        "session_id": f"session_{selected_persona['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "persona": selected_persona
                    }
                    st.session_state.current_session = session
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
                        
                        # AI応答生成
                        with st.spinner("応答を生成中..."):
                            # APIキーの取得
                            api_key = None
                            
                            # Streamlit Cloud環境でのAPIキー取得
                            if is_streamlit_cloud():
                                try:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                        else:
                                            st.warning("Streamlit Cloud環境でOpenAI APIキーが設定されていません")
                                    else:
                                        st.error("Streamlit Cloud環境でst.secretsが利用できません")
                                except Exception as e:
                                    st.error(f"Streamlit Cloud環境でのAPIキー取得に失敗: {str(e)}")
                            
                            # ローカル環境でのAPIキー確認
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception as e:
                                    st.error(f"ローカル環境でのAPIキー取得に失敗: {str(e)}")
                            
                            if api_key:
                                try:
                                    import openai
                                    client = openai.OpenAI(api_key=api_key)
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[
                                            {"role": "system", "content": f"あなたは{st.session_state.current_session['persona']['name']}というペルソナです。年齢{st.session_state.current_session['persona']['age']}歳、{st.session_state.current_session['persona']['gender']}、職業{st.session_state.current_session['persona']['occupation']}です。このペルソナの立場から自然に回答してください。"},
                                            {"role": "user", "content": user_message}
                                        ],
                                        max_tokens=200
                                    )
                                    ai_response = response.choices[0].message.content
                                except Exception as e:
                                    ai_response = f"申し訳ございません。現在、AI応答の生成に問題が発生しています。（エラー: {str(e)}）"
                            else:
                                ai_response = "OpenAI APIキーが設定されていないため、サンプル応答を表示します。実際のAI応答を利用するには、APIキーを設定してください。"
                            
                            # ペルソナの応答を追加
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": ai_response
                            })
                            st.rerun()
    
    else:  # 固定質問インタビュー（定量調査）
        st.subheader("📋 定量調査インタビュー")
        
        if st.session_state.personas:
            st.write("生成されたペルソナ全員に対して同じ質問を投げかけて、統計を取ります。")
            
            # 質問タイプの選択
            question_type = st.selectbox(
                "質問タイプを選択",
                ["選択式（ラジオボタン）", "選択式（チェックボックス）", "自由記述"]
            )
            
            # 質問入力
            if question_type == "選択式（ラジオボタン）":
                question_text = st.text_input("質問内容", placeholder="例：この商品カテゴリについてどのような印象をお持ちですか？")
                options = st.text_area("選択肢（1行に1つ）", placeholder="例：\nとても良い印象\n良い印象\n普通\n悪い印象\nとても悪い印象", height=100)
                
                if st.button("定量調査を実行", type="primary") and question_text and options:
                    option_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
                    
                    with st.spinner("定量調査を実行中..."):
                        # 全ペルソナに対して質問を実行
                        survey_results = []
                        
                        for persona in st.session_state.personas:
                            # APIキーの取得
                            api_key = None
                            
                            # Streamlit Cloud環境でのAPIキー取得
                            if is_streamlit_cloud():
                                try:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                        else:
                                            st.warning("Streamlit Cloud環境でOpenAI APIキーが設定されていません")
                                    else:
                                        st.error("Streamlit Cloud環境でst.secretsが利用できません")
                                except Exception as e:
                                    st.error(f"Streamlit Cloud環境でのAPIキー取得に失敗: {str(e)}")
                            
                            # ローカル環境でのAPIキー確認
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception as e:
                                    st.error(f"ローカル環境でのAPIキー取得に失敗: {str(e)}")
                            
                            if api_key:
                                try:
                                    import openai
                                    client = openai.OpenAI(api_key=api_key)
                                    
                                    prompt = f"""
                                    あなたは{persona['name']}というペルソナです。
                                    年齢{persona['age']}歳、{persona['gender']}、職業{persona.get('occupation', '会社員')}です。
                                    
                                    以下の質問に対して、提供された選択肢から1つを選んで回答してください。
                                    
                                    質問: {question_text}
                                    選択肢: {', '.join(option_list)}
                                    
                                    選択肢のみを回答してください。
                                    """
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=50
                                    )
                                    
                                    answer = response.choices[0].message.content.strip()
                                    # 選択肢に含まれていない場合は最初の選択肢を選択
                                    if answer not in option_list:
                                        answer = option_list[0]
                                    
                                except Exception as e:
                                    # エラーの場合はランダム選択
                                    import random
                                    answer = random.choice(option_list)
                            else:
                                # APIキーが設定されていない場合はランダム選択
                                import random
                                answer = random.choice(option_list)
                            
                            survey_results.append({
                                "persona": persona,
                                "question": question_text,
                                "answer": answer,
                                "options": option_list
                            })
                        
                        st.session_state.fixed_interviews = survey_results
                        st.success(f"{len(st.session_state.personas)}人のペルソナに定量調査を完了しました！")
                        st.rerun()
            
            elif question_type == "選択式（チェックボックス）":
                question_text = st.text_input("質問内容", placeholder="例：この商品カテゴリで重視する点は何ですか？（複数選択可）")
                options = st.text_area("選択肢（1行に1つ）", placeholder="例：\n価格\n品質\nデザイン\nブランド\n使いやすさ", height=100)
                
                if st.button("定量調査を実行", type="primary") and question_text and options:
                    option_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
                    
                    with st.spinner("定量調査を実行中..."):
                        survey_results = []
                        
                        for persona in st.session_state.personas:
                            # APIキーの取得
                            api_key = None
                            
                            # Streamlit Cloud環境でのAPIキー取得
                            if is_streamlit_cloud():
                                try:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                        else:
                                            st.warning("Streamlit Cloud環境でOpenAI APIキーが設定されていません")
                                    else:
                                        st.error("Streamlit Cloud環境でst.secretsが利用できません")
                                except Exception as e:
                                    st.error(f"Streamlit Cloud環境でのAPIキー取得に失敗: {str(e)}")
                            
                            # ローカル環境でのAPIキー確認
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception as e:
                                    st.error(f"ローカル環境でのAPIキー取得に失敗: {str(e)}")
                            
                            if api_key:
                                try:
                                    import openai
                                    client = openai.OpenAI(api_key=api_key)
                                    
                                    prompt = f"""
                                    あなたは{persona['name']}というペルソナです。
                                    年齢{persona['age']}歳、{persona['gender']}、職業{persona.get('occupation', '会社員')}です。
                                    
                                    以下の質問に対して、提供された選択肢から複数を選んで回答してください。
                                    
                                    質問: {question_text}
                                    選択肢: {', '.join(option_list)}
                                    
                                    選択した選択肢をカンマ区切りで回答してください。
                                    """
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=100
                                    )
                                    
                                    answer_text = response.choices[0].message.content.strip()
                                    selected_options = [opt.strip() for opt in answer_text.split(',') if opt.strip() in option_list]
                                    
                                    # 選択肢に含まれていない場合はランダム選択
                                    if not selected_options:
                                        import random
                                        selected_options = random.sample(option_list, min(2, len(option_list)))
                                    
                                except Exception as e:
                                    import random
                                    selected_options = random.sample(option_list, min(2, len(option_list)))
                            else:
                                import random
                                selected_options = random.sample(option_list, min(2, len(option_list)))
                            
                            survey_results.append({
                                "persona": persona,
                                "question": question_text,
                                "answer": selected_options,
                                "options": option_list
                            })
                        
                        st.session_state.fixed_interviews = survey_results
                        st.success(f"{len(st.session_state.personas)}人のペルソナに定量調査を完了しました！")
                        st.rerun()
            
            else:  # 自由記述
                question_text = st.text_input("質問内容", placeholder="例：この商品カテゴリについてどのような印象をお持ちですか？")
                
                if st.button("定量調査を実行", type="primary") and question_text:
                    with st.spinner("定量調査を実行中..."):
                        survey_results = []
                        
                        for persona in st.session_state.personas:
                            # APIキーの取得
                            api_key = None
                            
                            # Streamlit Cloud環境でのAPIキー取得
                            if is_streamlit_cloud():
                                try:
                                    if hasattr(st, 'secrets') and st.secrets is not None:
                                        if 'OPENAI_API_KEY' in st.secrets:
                                            api_key = st.secrets['OPENAI_API_KEY']
                                        else:
                                            st.warning("Streamlit Cloud環境でOpenAI APIキーが設定されていません")
                                    else:
                                        st.error("Streamlit Cloud環境でst.secretsが利用できません")
                                except Exception as e:
                                    st.error(f"Streamlit Cloud環境でのAPIキー取得に失敗: {str(e)}")
                            
                            # ローカル環境でのAPIキー確認
                            elif not is_streamlit_cloud():
                                try:
                                    import os
                                    from dotenv import load_dotenv
                                    load_dotenv()
                                    api_key = os.getenv('OPENAI_API_KEY')
                                except Exception as e:
                                    st.error(f"ローカル環境でのAPIキー取得に失敗: {str(e)}")
                            
                            if api_key:
                                try:
                                    import openai
                                    client = openai.OpenAI(api_key=api_key)
                                    
                                    prompt = f"""
                                    あなたは{persona['name']}というペルソナです。
                                    年齢{persona['age']}歳、{persona['gender']}、職業{persona.get('occupation', '会社員')}です。
                                    
                                    以下の質問に対して、このペルソナの立場から回答してください。
                                    
                                    質問: {question_text}
                                    
                                    簡潔に回答してください（50文字以内）。
                                    """
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": prompt}],
                                        max_tokens=100
                                    )
                                    
                                    answer = response.choices[0].message.content.strip()
                                    
                                except Exception as e:
                                    answer = f"これは{persona['name']}からのサンプル回答です。"
                            else:
                                answer = f"これは{persona['name']}からのサンプル回答です。"
                            
                            survey_results.append({
                                "persona": persona,
                                "question": question_text,
                                "answer": answer,
                                "options": []
                            })
                        
                        st.session_state.fixed_interviews = survey_results
                        st.success(f"{len(st.session_state.personas)}人のペルソナに定量調査を完了しました！")
                        st.rerun()
        
        # 定量調査結果の表示
        if st.session_state.fixed_interviews:
            st.subheader("📊 定量調査結果")
            
            # 統計情報の表示
            if st.session_state.fixed_interviews and len(st.session_state.fixed_interviews) > 0:
                first_result = st.session_state.fixed_interviews[0]
                
                if isinstance(first_result['answer'], list):  # チェックボックス形式
                    # 各選択肢の選択回数をカウント
                    option_counts = {}
                    for option in first_result['options']:
                        option_counts[option] = sum(1 for result in st.session_state.fixed_interviews if option in result['answer'])
                    
                    st.write("**選択肢別回答数:**")
                    for option, count in option_counts.items():
                        percentage = (count / len(st.session_state.fixed_interviews)) * 100
                        st.write(f"- {option}: {count}人 ({percentage:.1f}%)")
                    
                    # グラフ表示
                    import plotly.express as px
                    fig = px.bar(
                        x=list(option_counts.keys()),
                        y=list(option_counts.values()),
                        title="選択肢別回答数",
                        labels={'x': '選択肢', 'y': '回答数'}
                    )
                    st.plotly_chart(fig)
                    
                elif first_result['options']:  # ラジオボタン形式
                    # 各選択肢の選択回数をカウント
                    option_counts = {}
                    for option in first_result['options']:
                        option_counts[option] = sum(1 for result in st.session_state.fixed_interviews if result['answer'] == option)
                    
                    st.write("**選択肢別回答数:**")
                    for option, count in option_counts.items():
                        percentage = (count / len(st.session_state.fixed_interviews)) * 100
                        st.write(f"- {option}: {count}人 ({percentage:.1f}%)")
                    
                    # 円グラフ表示
                    import plotly.express as px
                    fig = px.pie(
                        values=list(option_counts.values()),
                        names=list(option_counts.keys()),
                        title="選択肢別回答率"
                    )
                    st.plotly_chart(fig)
                
                else:  # 自由記述形式
                    st.write("**回答一覧:**")
                    for result in st.session_state.fixed_interviews:
                        st.write(f"- **{result['persona']['name']}**: {result['answer']}")
            
            # 詳細結果の表示
            st.write("**詳細結果:**")
            for result in st.session_state.fixed_interviews:
                with st.expander(f"👤 {result['persona']['name']}の回答"):
                    st.write(f"**質問:** {result['question']}")
                    if isinstance(result['answer'], list):
                        st.write(f"**回答:** {', '.join(result['answer'])}")
                    else:
                        st.write(f"**回答:** {result['answer']}")
    
    # サマリー生成へ
    if st.button("結果サマリーを生成", type="primary"):
        st.session_state.current_step = 'summary'
        st.rerun()

# ステップ4: 結果サマリー
elif st.session_state.current_step == 'summary':
    st.markdown('<h2 class="section-header">📊 結果サマリー</h2>', unsafe_allow_html=True)
    
    if st.button("サマリーを生成", type="primary"):
        with st.spinner("サマリーを生成中..."):
            # Streamlit Cloud環境用のサンプルサマリー
            sample_summary = {
                "summary": {
                    "total_personas": len(st.session_state.personas),
                    "total_interviews": len(st.session_state.chat_messages) // 2 + len(st.session_state.fixed_interviews),
                    "key_insights": [
                        "サンプル洞察1: これはサンプルの洞察です。実際のAI分析を利用するには、Streamlit CloudのsecretsでOpenAI APIキーを設定してください。",
                        "サンプル洞察2: 実際のインタビュー結果に基づいた分析がここに表示されます。",
                        "サンプル洞察3: マーケティング戦略に活用できる具体的な洞察が含まれます。"
                    ],
                    "quantitative_results": {
                        "demographics": {
                            "age_distribution": {"20代": 2, "30代": 3},
                            "gender_distribution": {"女性": 3, "男性": 2}
                        }
                    },
                    "recommendations": [
                        "サンプル推奨事項1: これはサンプルの推奨事項です。",
                        "サンプル推奨事項2: 実際の調査結果に基づいた具体的な提案が含まれます。",
                        "サンプル推奨事項3: 実行可能なマーケティング戦略が提案されます。"
                    ]
                },
                "charts": {
                    "age_distribution": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                    "gender_distribution": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                }
            }
            st.session_state.summary = sample_summary
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
        
        # Excel出力（Streamlit Cloud環境用）
        if st.button("Excelファイルを出力", type="primary"):
            st.info("Streamlit Cloud環境では、Excelファイルの出力機能は利用できません。ローカル環境で実行するか、データを手動でコピーしてExcelに貼り付けてください。")
            
            # データの表示
            st.subheader("📊 出力データ")
            st.write("以下のデータをコピーしてExcelに貼り付けてください：")
            
            # 調査要件
            if st.session_state.survey_requirements:
                st.write("**調査要件:**")
                st.json(st.session_state.survey_requirements)
            
            # ペルソナ情報
            if st.session_state.personas:
                st.write("**ペルソナ情報:**")
                st.json(st.session_state.personas)

# フッター
st.divider()
st.caption("© 2024 仮想インタビューシステム v2.0.0") 
