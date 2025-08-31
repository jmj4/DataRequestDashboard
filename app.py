from pathlib import Path
import pandas as pd
from kiwipiepy import Kiwi
import streamlit as st
from utils import (
    open_excel_to_df,
    requests_by_dept,
    elapsed_time_by_dept,
    request_type_by_dept,
    request_classification_rules
    )


file_path = Path.cwd() / "data/requests_24_25.xlsx"


st.set_page_config(
    page_title="자료요청 대시보드",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="auto",
)

# 앱 타이틀
st.title("데이터 요청 처리 대시보드")


@st.cache_resource
def get_kiwi():
    return Kiwi()

@st.cache_data
def load_data(file_path) -> pd.DataFrame:
    return open_excel_to_df(file_path)

# 카테고리 분류를 위한 요청 토큰화
@st.cache_data
def tokenize_serializable(text: str):
    kiwi = get_kiwi()
    toks = kiwi.tokenize(text)
    return tuple((t.form, t.tag) for t in toks)

def classify_requests(sentence: str) -> str:
    token_pairs = tokenize_serializable(sentence)
    tokens = [form for form, tag in token_pairs if tag.startswith("NN")]
    match_counts = {
        category: sum(token in keyword for token in tokens)
        for category, keyword in request_classification_rules.items()
    }
    if max(match_counts.values()) > 0:
        return max(match_counts.items(), key=lambda x: x[1])[0]
    else:
        return "보고"


# 데이터 불러오기
data = load_data(file_path)

# 요청 분류 생성
data["요청문장"] = (data["요청목적"].fillna("") + data["요청사항"].fillna(""))
data["요청분류"] = data["요청문장"].apply(classify_requests)

# 센터, 기간 초기화
centers = sorted(data["센터명"].unique())
req_year, req_month = ["전체"], ["전체"]
req_year.extend(sorted(map(str, data['접수일'].dt.year.unique())))
req_month.extend(list(map(lambda x: str(x) + "월", range(1, 13))))


# session_state 기본값 설정
def set_session_state(param: str, default: str):
    if param not in st.session_state:
        st.session_state[param] = default
    if param in st.query_params:
        st.session_state[param] = st.query_params[param]

for key, default in [
    ("center", centers[0]),
    ("req_year", req_year[0]),
    ("req_month", req_month[0])
]:
    set_session_state(key, default)


# session_state 업데이트 함수
def update_param(param: str, select_key: str):
    st.session_state[param] = st.session_state[select_key]
    st.query_params[param] = st.session_state[select_key]


# 사이드 바
with st.sidebar:
    st.markdown("## 센터 및 기간 설정")
    st.selectbox(
        "센터명",
        centers,
        index=centers.index(st.session_state.center),
        key="center_select",
        on_change=lambda: update_param("center", "center_select")
    )
    st.selectbox(
        "년",
        req_year,
        index=req_year.index(st.session_state.req_year),
        key="year_select",
        on_change=lambda: update_param("req_year", "year_select")
    )
    st.selectbox(
        "월",
        req_month,
        index=req_month.index(st.session_state.req_month),
        key="month_select",
        on_change=lambda: update_param("req_month", "month_select")
    )


# 상단 레이아웃
total_requests = len(data)
met_3_days = sum(1 for d in data["기간"] if d <= 3)
met_3_days_rate = met_3_days / total_requests

mean_processing_days = data["기간"].mean()
top_departments_list = data[['센터명', '부서명']].value_counts().nlargest(1).index.to_list()


top_col_1, top_col_2 = st.columns(2, gap="large")
top_col_3, top_col_4 = st.columns(2, gap="large")
top_col_1.metric(label="누적 요청", value=f"{total_requests} 건", border=True)
top_col_2.metric(label="최다 요청 부서", value=f"{top_departments_list[0][0]} {top_departments_list[0][1]}", border=True)
top_col_3.metric(label="처리 기간 평균", value=f"{mean_processing_days:.1f} 일", border=True)
top_col_4.metric(label="3일 이내 처리 비율", value=f"{met_3_days_rate * 100:.0f} %", border=True)

st.markdown("---")


# 중단 레이아웃
st.markdown(f"## {st.session_state["req_year"]}년 {st.session_state["req_month"]}의 {st.session_state["center"]} 센터 요청")

filtered_data = data[data["센터명"] == st.session_state["center"]]

if st.session_state["req_year"] != "전체":
    filtered_data = filtered_data[filtered_data["접수일"].dt.year == int(st.session_state["req_year"])]

if st.session_state["req_month"] != "전체":
    filtered_data = filtered_data[filtered_data["접수일"].dt.month == int(st.session_state["req_month"][:-1])]


if filtered_data.empty or any(filtered_data["부서명"].isnull()):
    st.info("선택된 조건에 해당하는 데이터가 없습니다.", icon="🚨")
else:
    mid_col_1, mid_col_2 = st.columns(2, gap="large")
    selected_center = st.session_state["center"]

    with mid_col_1:
        request_pie_chart = requests_by_dept(filtered_data, selected_center)
        st.altair_chart(request_pie_chart, use_container_width=True)
    
    with mid_col_2:
        elapsed_time_bar_chart = elapsed_time_by_dept(filtered_data, selected_center)
        st.altair_chart(elapsed_time_bar_chart, use_container_width=True)

    request_type_bar_chart = request_type_by_dept(filtered_data, selected_center)
    st.altair_chart(request_type_bar_chart, use_container_width=True)