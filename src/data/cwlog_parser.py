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


def parse_cwlog(path: str):
    log = load_cwlog(path)
    meta_data, session_df = extract_session_meta(log)
    events_df = extract_events(log, meta_data)

    # 결과 확인
    print("=== session_df ===")
    print(session_df.head())
    print(session_df.columns)

    print("\n=== events_df ===")
    print(events_df.head())

    # 이전 session_df에서 기록된 event count와 실제로 df로 로드된 event count를 확인
    # 만약 여기서 다르다면 로드 단계 점검 필요
    print(f'length of events df: {len(events_df)}')
    print(f'recorded events: {session_df.loc[0, 'eventCount']}')

    # csv로 저장하기
    session_df.to_csv(f'res/csv/[csv_raw_session]_{session_df.loc[0, 'participantId']}_{session_df.loc[0, "taskId"]}.csv', index=False, encoding='utf-8-sig')
    events_df.to_csv(f'res/csv/[csv_raw_event]_{session_df.loc[0, 'participantId']}_{session_df.loc[0, "taskId"]}.csv', index=False, encoding='utf-8-sig')

    return session_df, events_df