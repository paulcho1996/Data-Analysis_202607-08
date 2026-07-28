import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="데이터셋 분석 도구",
    page_icon="📊",
    layout="wide",
)

st.title("📊 데이터셋 간편 분석 도구")
st.write("CSV 또는 Excel 파일을 업로드하면 기본 통계와 데이터 품질을 분석합니다.")

uploaded_file = st.file_uploader(
    "분석할 파일을 선택하세요.",
    type=["csv", "xlsx", "xls"],
)

if uploaded_file is None:
    st.info("CSV 또는 Excel 파일을 업로드해 주세요.")
    st.stop()


@st.cache_data
def load_data(file):
    """CSV 또는 Excel 파일을 DataFrame으로 읽습니다."""
    file_name = file.name.lower()

    if file_name.endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, encoding="cp949")

    return pd.read_excel(file)


try:
    df = load_data(uploaded_file)
except Exception as error:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {error}")
    st.stop()


# 기본 정보
st.subheader("1. 데이터 개요")

col1, col2, col3, col4 = st.columns(4)

col1.metric("행 개수", f"{len(df):,}")
col2.metric("열 개수", f"{len(df.columns):,}")
col3.metric("전체 결측값", f"{df.isna().sum().sum():,}")
col4.metric("중복 행", f"{df.duplicated().sum():,}")


# 원본 데이터
st.subheader("2. 데이터 미리보기")

number_of_rows = st.slider(
    "표시할 행 수",
    min_value=5,
    max_value=min(100, len(df)),
    value=min(20, len(df)),
)

st.dataframe(
    df.head(number_of_rows),
    use_container_width=True,
)


# 열 정보
st.subheader("3. 변수 정보")

column_information = pd.DataFrame({
    "변수명": df.columns,
    "데이터 유형": df.dtypes.astype(str).values,
    "결측값": df.isna().sum().values,
    "결측률(%)": (df.isna().mean().values * 100).round(2),
    "고유값 수": df.nunique(dropna=True).values,
})

st.dataframe(
    column_information,
    use_container_width=True,
    hide_index=True,
)


# 기술 통계
st.subheader("4. 기술통계")

try:
    descriptive_statistics = df.describe(include="all").transpose()
    st.dataframe(descriptive_statistics, use_container_width=True)
except Exception as error:
    st.warning(f"일부 기술통계를 계산하지 못했습니다: {error}")


# 결측치 분석
st.subheader("5. 결측치 분석")

missing_values = (
    df.isna()
    .sum()
    .sort_values(ascending=False)
    .rename("결측값")
    .to_frame()
)

missing_values["결측률(%)"] = (
    missing_values["결측값"] / len(df) * 100
).round(2)

st.dataframe(missing_values, use_container_width=True)

if missing_values["결측값"].sum() > 0:
    st.bar_chart(missing_values["결측값"])


# 숫자형 변수 분석
st.subheader("6. 숫자형 변수 분석")

numeric_columns = df.select_dtypes(include="number").columns.tolist()

if numeric_columns:
    selected_column = st.selectbox(
        "분석할 숫자형 변수를 선택하세요.",
        numeric_columns,
    )

    selected_data = df[selected_column].dropna()

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("평균", f"{selected_data.mean():,.2f}")
    metric2.metric("중앙값", f"{selected_data.median():,.2f}")
    metric3.metric("최솟값", f"{selected_data.min():,.2f}")
    metric4.metric("최댓값", f"{selected_data.max():,.2f}")

    st.line_chart(selected_data.reset_index(drop=True))
else:
    st.info("숫자형 변수가 없습니다.")


# 상관관계
if len(numeric_columns) >= 2:
    st.subheader("7. 상관관계")

    correlation = df[numeric_columns].corr()

    st.dataframe(
        correlation.style.background_gradient(cmap="RdBu", axis=None),
        use_container_width=True,
    )


# 분석 결과 다운로드
st.subheader("8. 분석 결과 내려받기")

summary_csv = column_information.to_csv(
    index=False,
).encode("utf-8-sig")

st.download_button(
    label="변수 분석 결과 CSV 다운로드",
    data=summary_csv,
    file_name="dataset_summary.csv",
    mime="text/csv",
)
