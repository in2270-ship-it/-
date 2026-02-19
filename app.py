import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# 웹페이지 기본 설정
st.set_page_config(page_title="업무 일지 관리 시스템", layout="wide")

# 관리자 비밀번호 설정 (원하시는 숫자로 변경 가능합니다)
ADMIN_PASSWORD = "1234" 

st.title("📊 임직원 업무 일지 및 실적 관리 시스템")
st.markdown("---")

DATA_FILE = "work_logs.csv"

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["작성일자", "작성자", "업무구분", "핵심 목표 및 계획", "진행상태", "달성률(%)", "미달성 사유 및 이슈"])
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 데이터 변환 함수들 ---
def list_to_string_with_check(inputs_list, checks_list):
    result = []
    for text, is_checked in zip(inputs_list, checks_list):
        if text.strip():
            mark = "[완료]" if is_checked else "[진행중]"
            result.append(f"{mark} {text.strip()}")
    return "\n\n".join(result)

def string_to_list_with_check(text, max_items):
    if not text or pd.isna(text): return [("", False)] * max_items
    parts = str(text).split("\n\n")
    items = []
    for p in parts:
        p = p.strip()
        if not p: continue
        is_checked = p.startswith("[완료]")
        content = p.replace("[완료]", "", 1).replace("[진행중]", "", 1).strip()
        items.append((content, is_checked))
    while len(items) < max_items: items.append(("", False))
    return items[:max_items]

def issues_to_string(lst):
    result = [f"{i+1}. {item.strip()}" for i, item in enumerate(lst) if item.strip()]
    return "\n\n".join(result)

def string_to_issues(text, max_items):
    if not text or pd.isna(text): return [""] * max_items
    parts = re.split(r'(?:^|\n)\d+\.\s*', str(text))
    items = [p.strip() for p in parts if p.strip()]
    while len(items) < max_items: items.append("")
    return items[:max_items]

tab1, tab2 = st.tabs(["[직원용] 업무 보고 및 수정", "[관리자용] 실적 대시보드"])

# ==========================================
# 1. [직원용 탭] (누구나 접속 가능)
# ==========================================
with tab1:
    mode = st.radio("작업 선택:", ["📝 신규 보고서 작성", "✏️ 기존 보고서 수정"], horizontal=True)
    if mode == "📝 신규 보고서 작성":
        with st.form("work_log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                emp_name = st.text_input("작성자 성명")
                task_type = st.selectbox("업무 구분", ["일일 업무", "주간 계획", "월간 계획"])
            with col2:
                date = st.date_input("작성 일자", datetime.today())
                status = st.selectbox("현재 진행 상태", ["진행 중", "완료"])
            
            st.markdown("##### 🎯 핵심 목표 및 계획")
            goal_inputs, goal_checks = [], []
            for i in range(1, 6):
                g1, g2, g3 = st.columns([0.5, 1.5, 13])
                with g1: st.write(f"{i}")
                with g2: goal_checks.append(st.checkbox("완료", key=f"n_chk_{i}"))
                with g3: goal_inputs.append(st.text_area(f"n_goal_{i}", height=100, label_visibility="collapsed"))
            
            st.markdown("##### ⚠️ 미달성 사유")
            issue_inputs = [st.text_area(f"n_issue_{i}", height=100, placeholder=f"{i}번 사유") for i in range(1, 4)]
            
            if st.form_submit_button("보고서 제출"):
                valid_cnt = sum(1 for t in goal_inputs if t.strip())
                chk_cnt = sum(1 for t, c in zip(goal_inputs, goal_checks) if t.strip() and c)
                rate = int((chk_cnt / valid_cnt) * 100) if valid_cnt > 0 else 0
                pd.DataFrame({"작성일자":[date],"작성자":[emp_name],"업무구분":[task_type],"핵심 목표 및 계획":[list_to_string_with_check(goal_inputs, goal_checks)],"진행상태":[status],"달성률(%)":[rate],"미달성 사유 및 이슈":[issues_to_string(issue_inputs)]}).to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                st.success("제출 완료!"); st.rerun()
    else:
        df_logs = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        event = st.dataframe(df_logs, use_container_width=True, on_select="rerun", selection_mode="single-row", key="emp_edit")
        if event.selection.rows:
            idx = df_logs.index[event.selection.rows[0]]
            row = df_logs.loc[idx]
            with st.form("edit_form"):
                en = st.text_input("성명", value=row["작성자"])
                eg_data = string_to_list_with_check(row["핵심 목표 및 계획"], 5)
                eg_in, eg_ch = [], []
                for i in range(5):
                    c1, c2, c3 = st.columns([0.5, 1.5, 13])
                    eg_ch.append(c2.checkbox("완료", value=eg_data[i][1], key=f"e_chk_{i}"))
                    eg_in.append(c3.text_area(f"e_g_{i}", value=eg_data[i][0], height=100))
                if st.form_submit_button("수정 저장"):
                    v_cnt = sum(1 for t in eg_in if t.strip()); c_cnt = sum(1 for t, c in zip(eg_in, eg_ch) if t.strip() and c)
                    df_logs.at[idx, "작성자"] = en; df_logs.at[idx, "달성률(%)"] = int((c_cnt/v_cnt)*100) if v_cnt>0 else 0
                    df_logs.at[idx, "핵심 목표 및 계획"] = list_to_string_with_check(eg_in, eg_ch)
                    df_logs.to_csv(DATA_FILE, index=False, encoding='utf-8-sig'); st.success("수정 완료!"); st.rerun()

# ==========================================
# 2. [관리자용 탭] (비밀번호 잠금)
# ==========================================
with tab2:
    st.subheader("🔐 관리자 전용 구역")
    # 비밀번호 입력창 (type="password"로 설정하여 글자가 별 모양으로 가려짐)
    pwd = st.text_input("관리자 비밀번호를 입력하세요:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("인증되었습니다.")
        try:
            df_logs = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            st.dataframe(df_logs, use_container_width=True)
            st.metric("전체 평균 달성률", f"{df_logs['달성률(%)'].mean():.1f}%")
        except: st.error("데이터 없음")
    elif pwd == "":
        st.info("비밀번호를 입력해 주세요.")
    else:
        st.error("비밀번호가 틀렸습니다. 접근 권한이 없습니다.")