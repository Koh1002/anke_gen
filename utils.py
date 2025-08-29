import pandas as pd
from typing import List, Dict, Any
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

def format_interview_results(interviews: List[Dict[str, Any]]) -> pd.DataFrame:
    """インタビュー結果をDataFrame形式に変換"""
    formatted_data = []
    for interview in interviews:
        formatted_data.append({
            "ペルソナ名": interview["persona"]["name"],
            "背景": interview["persona"]["background"],
            "質問": interview["question"],
            "回答": interview["answer"]
        })
    return pd.DataFrame(formatted_data)

def format_chat_messages(messages: List[Dict[str, Any]]) -> pd.DataFrame:
    """チャットメッセージをDataFrame形式に変換"""
    formatted_data = []
    for message in messages:
        formatted_data.append({
            "役割": message["role"],
            "メッセージ": message["content"],
            "タイムスタンプ": message["timestamp"]
        })
    return pd.DataFrame(formatted_data)

def format_personas(personas: List[Dict[str, Any]]) -> pd.DataFrame:
    """ペルソナ情報をDataFrame形式に変換"""
    formatted_data = []
    for persona in personas:
        formatted_data.append({
            "ID": persona["id"],
            "名前": persona["name"],
            "年齢": persona["age"],
            "性別": persona["gender"],
            "職業": persona["occupation"],
            "世帯構成": persona["household_composition"],
            "所得レベル": persona["income_level"],
            "ライフスタイル": persona["lifestyle"],
            "購買行動": persona["shopping_behavior"],
            "性格・特徴": persona["personality"]
        })
    return pd.DataFrame(formatted_data)

def save_to_excel(df: pd.DataFrame, filename: str = "interview_results.xlsx") -> str:
    """DataFrameをExcelファイルとして保存"""
    df.to_excel(filename, index=False, engine="openpyxl")
    return filename

def parse_interview_response(response: str) -> Dict[str, Any]:
    """インタビュー応答をパース"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # JSONとしてパースできない場合は、テキストとして処理
        return {
            "summary": response,
            "interviews": [],
            "personas": []
        }

def create_demographics_chart(personas: List[Dict[str, Any]], chart_type: str = "age") -> str:
    """人口統計チャートを生成"""
    # 日本語フォント設定
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
    sns.set_style("whitegrid")
    
    if chart_type == "age":
        # 年齢分布
        ages = [p["age"] for p in personas]
        age_groups = [f"{(age // 10) * 10}代" for age in ages]
        age_counts = pd.Series(age_groups).value_counts()
        
        plt.figure(figsize=(10, 6))
        age_counts.plot(kind='bar', color='skyblue')
        plt.title('年齢分布', fontsize=14, fontweight='bold')
        plt.xlabel('年齢層')
        plt.ylabel('人数')
        plt.xticks(rotation=45)
        
    elif chart_type == "gender":
        # 性別分布
        genders = [p["gender"] for p in personas]
        gender_counts = pd.Series(genders).value_counts()
        
        plt.figure(figsize=(8, 8))
        plt.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title('性別分布', fontsize=14, fontweight='bold')
    
    # グラフをBase64エンコード
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return chart_base64

def generate_summary_statistics(personas: List[Dict[str, Any]], interviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """サマリー統計を生成"""
    stats = {
        "total_personas": len(personas),
        "total_interviews": len(interviews),
        "demographics": {
            "age_distribution": {},
            "gender_distribution": {},
            "occupation_distribution": {}
        }
    }
    
    # 年齢分布
    age_groups = {}
    for persona in personas:
        age_group = f"{(persona['age'] // 10) * 10}代"
        age_groups[age_group] = age_groups.get(age_group, 0) + 1
    stats["demographics"]["age_distribution"] = age_groups
    
    # 性別分布
    gender_counts = {}
    for persona in personas:
        gender_counts[persona['gender']] = gender_counts.get(persona['gender'], 0) + 1
    stats["demographics"]["gender_distribution"] = gender_counts
    
    # 職業分布
    occupation_counts = {}
    for persona in personas:
        occupation_counts[persona['occupation']] = occupation_counts.get(persona['occupation'], 0) + 1
    stats["demographics"]["occupation_distribution"] = occupation_counts
    
    return stats

def validate_survey_requirements(requirements: Dict[str, Any]) -> bool:
    """調査要件の妥当性をチェック"""
    required_fields = ["product_category", "target_age_range", "target_gender", "survey_purpose"]
    
    for field in required_fields:
        if field not in requirements or not requirements[field]:
            return False
    
    return True

def format_fixed_interview_results(interviews: List[Dict[str, Any]]) -> pd.DataFrame:
    """固定質問インタビュー結果をDataFrame形式に変換"""
    formatted_data = []
    for interview in interviews:
        for i, (question, answer) in enumerate(zip(interview['questions'], interview['answers'])):
            formatted_data.append({
                "ペルソナ名": interview['persona']['name'],
                "年齢": interview['persona']['age'],
                "性別": interview['persona']['gender'],
                "職業": interview['persona']['occupation'],
                "質問番号": i + 1,
                "質問": question,
                "回答": answer
            })
    return pd.DataFrame(formatted_data) 