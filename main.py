from src.data.cwlog_parser import *


total_sessions_df = pd.DataFrame(columns=SESSIONS_DF_COLUMNS)
total_events_df = pd.DataFrame(columns=EVENTS_DF_COLUMNS)
for file_path in LOG_PATH.iterdir():
    # 확장자 확인
    if file_path.suffix == '.json':
        tmp_sessions_df, tmp_events_df = parse_cwlog(file_path, csv_save=False)
        total_sessions_df = pd.concat([total_sessions_df, tmp_sessions_df])
        total_events_df = pd.concat([total_events_df, tmp_events_df])

total_sessions_df = total_sessions_df.reset_index(drop=True)
total_events_df = total_events_df.reset_index(drop=True)

total_sessions_df = total_sessions_df[ORDERED_SESSIONS_DF_COLUMNS]
total_events_df = total_events_df[ORDERED_EVENTS_DF_COLUMNS]

# 파일 확인 용도
total_events_df.to_excel(CSV_PATH.joinpath('total_events_df.xlsx'), index=False)
total_sessions_df.to_excel(CSV_PATH.joinpath('total_sessions_df.xlsx'), index=False)