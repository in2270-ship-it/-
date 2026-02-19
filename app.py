import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# 웹페이지 기본 설정
st.set_page_config(page_title="업무 일지 관리 시스템", layout="wide")

st.title("📊 임직원 업무 일지 및 실적 관리 시스템")
st.markdown("---")

# 데이터 저장을 위한 CSV 파일 설정
DATA_FILE = "work_logs.csv"

# 파일이 없으면 새로 생성
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["작성일자", "작성자", "업무구분", "핵심 목표 및 계획", "진행상태", "달성률(%)", "미달성 사유 및 이슈"])
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 표 데이터를 다루기 위한 변환 함수 (체크박스 인식 기능 추가) ---
def list_to_string_with_check(inputs_list, checks_list):
    result = []
    for text, is_checked in zip(inputs_list, checks_list):
        if text.strip():
            mark = "[완료]" if is_checked else "[진행중]"
            result.append(f"{mark} {text.strip()}")
    return "\n\n".join(result)

def string_to_list_with_check(text, max_items):
    if not text or pd.isna(text):
        return [("", False)] * max_items
    
    parts = str(text).split("\n\n")
    items = []
    for p in parts:
        p = p.strip()
        if not p: continue
        
        is_checked = False
        if p.startswith("[완료]"):
            is_checked = True
            content = p.replace("[완료]", "", 1).strip()
        elif p.startswith("[진행중]"):
            content = p.replace("[진행중]", "", 1).strip()
        else:
            # 예전에 작성된 테스트 데이터 호환용
            content = re.sub(r'^\d+\.\s*', '', p).strip()
            
        items.append((content, is_checked))
        
    while len(items) < max_items:
        items.append(("", False))
    return items[:max_items]

def issues_to_string(lst):
    result = []
    for i, item in enumerate(lst):
        if item.strip():
            result.append(f"{i+1}. {item.strip()}")
    return "\n\n".join(result)

def string_to_issues(text, max_items):
    if not text or pd.isna(text):
        return [""] * max_items
    parts = re.split(r'(?:^|\n)\d+\.\s*', str(text))
    items = [p.strip() for p in parts if p.strip()]
    while len(items) < max_items:
        items.append("")
    return items[:max_items]

tab1, tab2 = st.tabs(["[직원용] 업무 보고 및 수정", "[관리자용] 실적 대시보드"])

# ==========================================
# 1. [직원용 탭] : 신규 작성 및 본인 보고서 수정
# ==========================================
with tab1:
    mode = st.radio("원하시는 작업을 선택하세요:", ["📝 신규 보고서 작성", "✏️ 기존 보고서 수정"], horizontal=True)
    st.markdown("---")
    
    if mode == "📝 신규 보고서 작성":
        st.subheader("📝 신규 업무 보고 작성")
        st.caption("달성률(%)은 목표 목록의 '완료' 체크 개수에 따라 시스템이 얄짤없이 자동 계산합니다.")
        
        with st.form("work_log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                emp_name = st.text_input("작성자 성명", placeholder="예: 홍길동 대리")
                task_type = st.selectbox("업무 구분", ["일일 업무", "주간 계획", "월간 계획"])
            with col2:
                date = st.date_input("작성 일자", datetime.today())
                status = st.selectbox("현재 진행 상태", ["진행 중", "완료"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # [맞춤형 표 1] 체크박스 + 넉넉한 글쓰기 칸
            st.markdown("##### 🎯 핵심 목표 및 계획 (최대 5개 항목)")
            st.info("💡 작성하신 목표 중 좌측의 [완료] 박스를 체크한 비율만큼 달성률(%)이 자동 계산됩니다.")
            
            goal_inputs = []
            goal_checks = []
            for i in range(1, 6):
                # 순서(0.5) : 체크박스(1.5) : 내용(13) 비율로 나눔
                g_col1, g_col2, g_col3 = st.columns([0.5, 1.5, 13]) 
                with g_col1:
                    st.markdown(f"<div style='text-align:center; padding-top:15px; font-weight:bold; color:gray;'>{i}</div>", unsafe_allow_html=True)
                with g_col2:
                    st.markdown("<div style='padding-top:10px;'>", unsafe_allow_html=True)
                    chk = st.checkbox("완료", key=f"goal_chk_{i}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    goal_checks.append(chk)
                with g_col3:
                    val = st.text_area(f"goal_new_{i}", height=100, label_visibility="collapsed", placeholder=f"{i}번 목표를 자유롭게 입력하세요")
                    goal_inputs.append(val)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # [맞춤형 표 2] 미달성 사유
            st.markdown("##### ⚠️ 미달성 사유 및 특이사항 (지연 시 필수 작성)")
            issue_inputs = []
            for i in range(1, 4):
                i_col1, i_col2 = st.columns([0.5, 14.5])
                with i_col1:
                    st.markdown(f"<div style='text-align:center; padding-top:15px; font-weight:bold; color:gray;'>{i}</div>", unsafe_allow_html=True)
                with i_col2:
                    val = st.text_area(f"issue_new_{i}", height=100, label_visibility="collapsed", placeholder=f"{i}번 특이사항을 입력하세요")
                    issue_inputs.append(val)
            
            submitted = st.form_submit_button("보고서 제출하기 (달성률 자동 계산)")
            
            if submitted:
                # 1. 빈칸 무시하고 작성된 데이터만 모으기
                task_plan = list_to_string_with_check(goal_inputs, goal_checks)
                issue_reason = issues_to_string(issue_inputs)
                
                # 2. 깐깐한 달성률(%) 자동 계산 로직
                valid_goals_count = sum(1 for text in goal_inputs if text.strip())
                checked_goals_count = sum(1 for text, chk in zip(goal_inputs, goal_checks) if text.strip() and chk)
                
                if valid_goals_count > 0:
                    auto_completion_rate = int((checked_goals_count / valid_goals_count) * 100)
                else:
                    auto_completion_rate = 0
                
                if not emp_name or valid_goals_count == 0:
                    st.error("작성자 성명과 핵심 목표(최소 1칸 이상)는 필수 입력 항목입니다.")
                else:
                    new_data = pd.DataFrame({
                        "작성일자": [date], "작성자": [emp_name], "업무구분": [task_type],
                        "핵심 목표 및 계획": [task_plan], "진행상태": [status],
                        "달성률(%)": [auto_completion_rate], "미달성 사유 및 이슈": [issue_reason]
                    })
                    new_data.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                    st.success(f"✅ {emp_name}님의 업무 보고가 제출되었습니다. (시스템 산출 달성률: {auto_completion_rate}%)")
                    st.rerun() 

    else: 
        st.subheader("✏️ 내 보고서 찾아 진행상황 업데이트 (수정)")
        st.caption("목표를 추가로 완수했다면 아래 표를 클릭해 체크박스를 마저 채워주세요.")
        
        df_logs = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        
        if df_logs.empty:
            st.info("아직 제출된 업무 보고가 없습니다.")
        else:
            event = st.dataframe(df_logs, use_container_width=True, on_select="rerun", selection_mode="single-row", key="employee_table")
            selected_rows = event.selection.rows
            
            if selected_rows: 
                actual_idx = df_logs.index[selected_rows[0]]
                sel_row = df_logs.loc[actual_idx]
                
                st.markdown(f"#### 🔍 [{sel_row['작성자']}]님의 보고서 수정")
                
                with st.form("edit_form"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        e_name = st.text_input("작성자 성명", value=sel_row["작성자"])
                        e_type = st.selectbox("업무 구분", ["일일 업무", "주간 계획", "월간 계획"], index=["일일 업무", "주간 계획", "월간 계획"].index(sel_row["업무구분"]) if sel_row["업무구분"] in ["일일 업무", "주간 계획", "월간 계획"] else 0)
                    with e_col2:
                        e_date = st.text_input("작성 일자", value=sel_row["작성일자"])
                        e_status = st.selectbox("현재 진행 상태", ["진행 중", "완료"], index=["진행 중", "완료"].index(sel_row["진행상태"]) if sel_row["진행상태"] in ["진행 중", "완료"] else 0)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    st.markdown("##### 🎯 핵심 목표 진행상황 업데이트")
                    goals_data = string_to_list_with_check(sel_row["핵심 목표 및 계획"], 5)
                    edit_goal_inputs = []
                    edit_goal_checks = []
                    
                    for i in range(1, 6):
                        eg_col1, eg_col2, eg_col3 = st.columns([0.5, 1.5, 13])
                        content, is_chk = goals_data[i-1]
                        with eg_col1:
                            st.markdown(f"<div style='text-align:center; padding-top:15px; font-weight:bold; color:gray;'>{i}</div>", unsafe_allow_html=True)
                        with eg_col2:
                            st.markdown("<div style='padding-top:10px;'>", unsafe_allow_html=True)
                            chk = st.checkbox("완료", value=is_chk, key=f"edit_chk_{i}")
                            st.markdown("</div>", unsafe_allow_html=True)
                            edit_goal_checks.append(chk)
                        with eg_col3:
                            val = st.text_area(f"goal_edit_{i}", value=content, height=100, label_visibility="collapsed")
                            edit_goal_inputs.append(val)
                    
                    st.markdown("##### ⚠️ 미달성 사유 및 특이사항 수정")
                    issues_data = string_to_issues(sel_row["미달성 사유 및 이슈"], 3)
                    edit_issue_inputs = []
                    for i in range(1, 4):
                        ei_col1, ei_col2 = st.columns([0.5, 14.5])
                        with ei_col1:
                            st.markdown(f"<div style='text-align:center; padding-top:15px; font-weight:bold; color:gray;'>{i}</div>", unsafe_allow_html=True)
                        with ei_col2:
                            val = st.text_area(f"issue_edit_{i}", value=issues_data[i-1], height=100, label_visibility="collapsed")
                            edit_issue_inputs.append(val)
                    
                    update_btn = st.form_submit_button("수정 및 달성률 재계산 저장")
                    
                    if update_btn:
                        valid_goals_count = sum(1 for text in edit_goal_inputs if text.strip())
                        checked_goals_count = sum(1 for text, chk in zip(edit_goal_inputs, edit_goal_checks) if text.strip() and chk)
                        auto_completion_rate = int((checked_goals_count / valid_goals_count) * 100) if valid_goals_count > 0 else 0
                        
                        df_logs.at[actual_idx, "작성자"] = e_name
                        df_logs.at[actual_idx, "업무구분"] = e_type
                        df_logs.at[actual_idx, "진행상태"] = e_status
                        df_logs.at[actual_idx, "작성일자"] = e_date
                        df_logs.at[actual_idx, "달성률(%)"] = auto_completion_rate
                        df_logs.at[actual_idx, "핵심 목표 및 계획"] = list_to_string_with_check(edit_goal_inputs, edit_goal_checks)
                        df_logs.at[actual_idx, "미달성 사유 및 이슈"] = issues_to_string(edit_issue_inputs)
                        
                        df_logs.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                        st.success("✅ 진행상황이 성공적으로 업데이트되었습니다.")
                        st.rerun()

# ==========================================
# 2. [관리자용 탭] : 조회 및 상세 내용 읽기 전용
# ==========================================
with tab2:
    st.subheader("📈 임직원 실적 및 이행률 모니터링")
    
    try:
        df_logs = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        
        if df_logs.empty:
            st.info("아직 제출된 업무 보고가 없습니다.")
        else:
            st.markdown("##### 📌 데이터 필터링 (원하는 조건만 골라보기)")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_type = st.multiselect("업무 구분", ["일일 업무", "주간 계획", "월간 계획"], default=["일일 업무", "주간 계획", "월간 계획"])
            with f_col2:
                filter_status = st.multiselect("진행 상태", ["진행 중", "완료"], default=["진행 중", "완료"])
            
            filtered_df = df_logs[
                (df_logs["업무구분"].isin(filter_type)) & 
                (df_logs["진행상태"].isin(filter_status))
            ]
            
            st.markdown("##### 🖱️ [클릭] 내용이 긴 보고서는 아래 표를 클릭하시면 전체 내용을 볼 수 있습니다.")
            event = st.dataframe(filtered_df, use_container_width=True, on_select="rerun", selection_mode="single-row", key="admin_table")
            
            st.markdown("---")
            
            selected_rows = event.selection.rows
            
            if selected_rows: 
                actual_idx = filtered_df.index[selected_rows[0]]
                sel_row = df_logs.loc[actual_idx]
                
                st.subheader(f"🔍 [{sel_row['작성자']}] 업무 보고서 상세 보기 (수정 불가)")
                
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("작성 일자", sel_row['작성일자'])
                m_col2.metric("업무 구분", sel_row['업무구분'])
                m_col3.metric("진행 상태", sel_row['진행상태'])
                
                # 시스템이 자동 계산한 얄짤없는 달성률 표시
                m_col4.metric("📊 시스템 계산 달성률", f"{sel_row['달성률(%)']}%")
                
                st.text_area("🎯 핵심 목표 및 계획 (제출 내용)", value=sel_row["핵심 목표 및 계획"], height=250, disabled=True)
                st.text_area("⚠️ 미달성 사유 및 특이사항", value=sel_row["미달성 사유 및 이슈"] if pd.notna(sel_row["미달성 사유 및 이슈"]) else "입력된 특이사항 없음", height=150, disabled=True)
                
            st.markdown("---")
            avg_rate = df_logs["달성률(%)"].mean()
            st.metric(label="전체 임직원 평균 업무 달성률", value=f"{avg_rate:.1f}%")
            
    except FileNotFoundError:
         st.error("데이터 파일을 찾을 수 없습니다.")