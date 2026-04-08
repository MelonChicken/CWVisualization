from pathlib import Path
import pandas as pd
import json
from src.config.config import *


def load_cwlog(path: str | Path):

    path = Path(path)

    # 절대경로면 그대로 사용, 상대경로면 LOG_PATH 기준으로 해석
    if path.is_absolute():
        file_path = path
    else:
        file_path = LOG_PATH / path

    # file load
    with open(file_path, "r", encoding="utf-8") as f:
        log = json.load(f)
    return log

def extract_session_meta(log):


    # events 열과 나머지 메타 데이터 (예: 실험 정보)를 분리
    meta_data = {key: value for key, value in log.items() if key != 'events'}


    # DataFrame 형태로 변환 (딕셔너리 1개를 원소로 가진 리스트 -> DataFrame)
    session_df = pd.DataFrame([meta_data])

    return meta_data, session_df

def extract_events(log, meta_data):
    # 식별 가능한 최소한의 Id 정보만 같이 저장
    events = log.get('events', []) # list[] 형태로 반환

    # events -> 여러 행 dataframe으로 변환
    events_df = pd.json_normalize(events)


    # 5. 나중에 조인할 수 있도록 key 추가
    for key in ['participantId', 'taskId']:
        if key in meta_data:
            events_df[key] = meta_data[key]

    return events_df


def parse_cwlog(path: str | Path, csv_save: bool = True):
    log = load_cwlog(path)
    meta_data, session_df = extract_session_meta(log)
    events_df = extract_events(log, meta_data)

    # 결과 확인
    # print("=== session_df ===")
    # print(session_df.head())
    # print(session_df.columns)
    #
    # print("\n=== events_df ===")
    # print(events_df.head())

    # 이전 session_df에서 기록된 event count와 실제로 df로 로드된 event count를 확인
    # 만약 여기서 다르다면 로드 단계 점검 필요
    # print(f'length of events df: {len(events_df)}')
    # print(f'recorded events: {session_df.loc[0, 'eventCount']}')
    if csv_save:
        # csv로 저장하기
        session_df.to_csv(f'res/csv/[csv_raw_session]_{session_df.loc[0, 'participantId']}_{session_df.loc[0, "taskId"]}.csv', index=False, encoding='utf-8-sig')
        events_df.to_csv(f'res/csv/[csv_raw_event]_{session_df.loc[0, 'participantId']}_{session_df.loc[0, "taskId"]}.csv', index=False, encoding='utf-8-sig')

    return session_df, events_df

def parse_cwlog_all(csv_save: bool = True):

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
    total_events_df['index'] = total_events_df['participantId'] + '-' + total_events_df['taskId']
    total_events_df.rename(columns={'index': 'PID-TID'}, inplace=True)

    total_sessions_df = convert_sessions_total_dtypes(total_sessions_df)
    total_events_df = convert_events_total_dtypes(total_events_df)
    if csv_save:
        # 파일 확인 용도
        total_events_df.to_csv(CSV_PATH.joinpath('total_events_df.csv'), index=False)
        total_sessions_df.to_csv(CSV_PATH.joinpath('total_sessions_df.csv'), index=False)
    return total_sessions_df, total_events_df

def convert_sessions_total_dtypes(sessions_df):
    string_cols = [
        "participantId", "taskId", "sessionId", "tabId",
        "startedUrl", "endedUrl", "navigationStack", "userAgent"
    ]
    int_cols = [
        "startTimeMs", "endTimeMs", "navigationIndex", "eventCount"
    ]

    for col in string_cols:
        if col in sessions_df.columns:
            sessions_df[col] = sessions_df[col].astype("string")

    for col in int_cols:
        if col in sessions_df.columns:
            sessions_df[col] = pd.to_numeric(sessions_df[col], errors="coerce").astype("Int64")

    if "startTime" in sessions_df.columns:
        sessions_df["startTime"] = pd.to_datetime(
            sessions_df["startTime"],
            format="%y-%m-%d %H:%M:%S",
            errors="coerce"
        )
        sessions_df["startTime"] = sessions_df["startTime"].dt.tz_localize("Asia/Seoul")

    sessions_df["endTime"] = pd.to_datetime(
        sessions_df["endTime"],
        format="%y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    sessions_df["endTime"] = sessions_df["endTime"].dt.tz_localize("Asia/Seoul")

    if "endTime" in sessions_df.columns:
        pass

    return sessions_df

def convert_events_total_dtypes(events_df):
    string_cols = [
        "PID-TID", "type", "url", "title", "tagName", "className",
        "text", "selector", "id", "href", "visibilityState",
        "name", "role", "inputType", "selectedText",
        "participantId", "taskId", "code", "navigationType",
        "historyTraversal", "key", "maskedValue"
    ]

    int_cols = [
        "elapsedMs", "delay", "viewportWidth", "viewportHeight",
        "button", "valueLength", "timestampMs"
    ]

    float_cols = [
        "scrollX", "scrollY", "x", "y", "pageX", "pageY"
    ]

    bool_cols = [
        "metaKey", "checked", "ctrlKey", "altKey", "shiftKey"
    ]

    for col in string_cols:
        if col in events_df.columns:
            events_df[col] = events_df[col].astype("string")

    for col in int_cols:
        if col in events_df.columns:
            events_df[col] = pd.to_numeric(events_df[col], errors="coerce").astype("Int64")

    for col in float_cols:
        if col in events_df.columns:
            events_df[col] = pd.to_numeric(events_df[col], errors="coerce").astype("Float64")

    for col in bool_cols:
        if col in events_df.columns:
            events_df[col] = (
                events_df[col]
                .astype("string")
                .str.strip()
                .str.lower()
                .map({
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False
                })
                .astype("boolean")
            )

    if "timestamp" in events_df.columns:
        events_df["timestamp"] = pd.to_datetime(
            events_df["timestamp"],
            format="%y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        events_df["timestamp"] = events_df["timestamp"].dt.tz_localize("Asia/Seoul")

    return events_df