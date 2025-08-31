from pathlib import Path
import pandas as pd
from utils import open_excel_to_df, save_df_to_excel


load_file_path = Path.cwd() / "data/24_자료요청서.xlsx"
save_file_path = Path.cwd() / "data/requests_24_25.xlsx"


def preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임의 각 컬럼을 전처리함
    엑셀에서 직접 처리 시 이 함수는 불필요함

    Arg:
        df: 입력 DataFrame
    Return:
        전처리된 DataFrame
    """

    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    # 엑셀에서 처리 시 해당 부분이 필요 없을 수 있음
    df['접수일'] = pd.to_datetime(df['접수일'], format="%Y-%m-%d")
    df['제공날짜'] = pd.to_datetime(df['제공날짜'], format="%Y-%m-%d")
    df['기간'] = (df['제공날짜'] - df['접수일']).dt.days
    df['기안제목'] = df['기안제목'].str.replace(r"\[.*?\]\s*", "", regex=True)
    
    df = df[['접수일', '제공날짜', '기간', '센터명', '부서명', '요청자', '직위', '기안번호', '기안제목', '요청목적', '요청사항']]
    
    return df


def main():    
    raw_data = open_excel_to_df(load_file_path)

    preprocessed_df = preprocessing(raw_data)

    save_df_to_excel(preprocessed_df, save_file_path)


if __name__ == "__main__":
    main()