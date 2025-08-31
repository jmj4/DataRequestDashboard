from pathlib import Path
import xlwings as xw
import pandas as pd
import altair as alt


request_classification_rules = {
    "운영":["접수", "센터별", "연기"],
    "경영":["매출", "비용", "성과"],
    "연구":["연구", "분석", "통계"],
    "행정":["보고", "제출", "감사", "기안"],
    "개발":["SQL", "쿼리", "자동화", "기능"],
    "품질":["오류", "장애", "품질", "리스크"]
}


def open_excel_to_df(file_path: Path) -> pd.DataFrame:
    """
    xlwings를 사용하여 엑셀파일을 열어 DataFrame으로 변경함

    Arg:
        file_path: 엑셀 파일 위치
    Return:
        변환된 DataFrame
    """

    app = xw.App(visible=False)
    book = app.books.open(file_path)
    sheet = book.sheets[0]
    
    df = sheet.range("A1").options(
        pd.DataFrame,
        header=1,
        index=False,
        expand="table"
    ).value
    book.close()
    app.quit()
    
    return df


def save_df_to_excel(df: pd.DataFrame, file_path: Path):
    """
    작업한 DataFrame을 엑셀 파일로 저장함
    
    Args:
        df: DataFrame
        file_path: 엑셀 파일 저장 위치
    """

    app = xw.App(visible=False)
    book = app.books.add()
    sheet = book.sheets[0]

    sheet.range("A1").options(
        index=False,
        header=True
    ).value = df
    book.save(file_path)
    book.close()
    app.quit()


def requests_by_dept(df: pd.DataFrame, center: str) -> alt.Chart:
    counts = (
        df
        .groupby("부서명")
        .size()
        .reset_index(name="요청건수")
    )

    counts["percent"] = (counts["요청건수"] / counts["요청건수"].sum() * 100).map(lambda x: f"{x:.0f}%")

    base = (
        alt.Chart(counts)
        .encode(
            theta=alt.Theta("요청건수:Q", stack=True),
            color=alt.Color("부서명:N", legend=alt.Legend(title="부서명")),
            tooltip=["부서명", "요청건수", "percent"]
        ).properties(
            title=f"{center} 센터의 부서별 요청 비율"
        )
    )

    chart = base.mark_arc(outerRadius=120)
    # text = base.mark_text(radius=180, size=16).encode(text="부서명:N")

    return chart


def elapsed_time_by_dept(df: pd.DataFrame, center: str) -> alt.Chart:
    counts = (
        df
        .groupby("부서명")["기간"]
        .mean()
        .reset_index()
        .sort_values(by="기간")
    )

    chart = (
        alt.Chart(counts)
        .mark_bar(color="skyblue", stroke="black")
        .encode(
            x=alt.X("기간:Q", title="평균 처리일수(일)"),
            y=alt.Y("부서명:N", sort=alt.EncodingSortField(field="기간", order="ascending"), title="부서명"),
            tooltip=["부서명", "기간"]
        ).properties(
            title=f"{center} 센터의 부서별 평균 처리일수"
        )
    )

    return chart


def request_type_by_dept(df: pd.DataFrame, center: str) -> alt.Chart:
    counts = (
        df
        .groupby(["부서명", "요청분류"])
        .size()
        .reset_index(name="요청건수")
    )

    chart = (
        alt.Chart(counts)
        .mark_bar(size=20)
        .encode(
            x=alt.X(
                "부서명:N",
                axis=alt.Axis(
                    labelAngle=-45,
                    tickMinStep=1,
                    values=counts["부서명"].unique().tolist(),
                )
            ),
            y=alt.Y("요청건수:Q"),
            color=alt.Color(
                "요청분류:N",
                scale=alt.Scale(scheme="tableau20"),
            ),
            tooltip=["부서명", "요청분류", "요청건수"]
        ).properties(
            title=f"{center} 센터의 부서별 요청 분류",
        )
    )

    return chart