from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CSV_PATH = PROJECT_ROOT / 'res' / 'csv'
LOG_PATH = PROJECT_ROOT / 'res' / 'log'

# RAW COLUMNS FOR RAW DATA
# 40 columns
EVENTS_DF_COLUMNS = [
    'index','type','timestamp','elapsedMs','delay',
    'url','title','viewportWidth','viewportHeight','scrollX',
    'scrollY','x','y','pageX','pageY','button',
    'tagName','className','text','selector','id',
    'href','visibilityState','name','role','inputType',
    'selectedText','participantId','taskId','metaKey', 'code',
    'navigationType', 'checked', 'ctrlKey', 'historyTraversal', 'valueLength',
    'key', 'maskedValue', 'altKey', 'shiftKey', 'timestampMs'
]

#14 Columns
SESSIONS_DF_COLUMNS = [
    'participantId','taskId','sessionId','tabId','startTime',
    'endTime','startedUrl','endedUrl','userAgent','eventCount',
    'endTimeMs', 'navigationIndex', 'navigationStack', 'startTimeMs'
]

# ORDERED COLUMNS FOR EASY-READ

ORDERED_EVENTS_DF_COLUMNS =  [
    # 1. 기본 식별 정보
    'index', 'participantId', 'taskId',

    # 2. 시간 정보
    'timestamp', 'timestampMs', 'elapsedMs', 'delay',

    # 3. 이벤트 기본 정보
    'type', 'navigationType', 'historyTraversal', 'visibilityState',

    # 4. 페이지 문맥 정보
    'url', 'title', 'viewportWidth', 'viewportHeight', 'scrollX', 'scrollY',

    # 5. 대상 요소 정보
    'tagName', 'id', 'className', 'name', 'role', 'selector', 'text', 'href',

    # 6. 마우스/포인터 위치 정보
    'x', 'y', 'pageX', 'pageY', 'button',

    # 7. 키보드 입력 정보
    'key', 'code', 'ctrlKey', 'shiftKey', 'altKey', 'metaKey',

    # 8. 입력 필드/폼 관련 정보
    'inputType', 'checked', 'selectedText', 'maskedValue', 'valueLength'
]

ORDERED_SESSIONS_DF_COLUMNS = [
    # 1. 기본 식별 정보
    'participantId', 'taskId', 'sessionId', 'tabId',

    # 2. 시간 정보
    'startTime', 'startTimeMs', 'endTime', 'endTimeMs',

    # 3. 시작/종료 페이지 문맥
    'startedUrl', 'endedUrl',

    # 4. 세션 내 탐색 흐름 정보
    'navigationIndex', 'navigationStack',

    # 5. 세션 집계 정보
    'eventCount',

    # 6. 환경 정보
    'userAgent'
]

# 빠진 것 없는지 확인
# print(set(EVENTS_DF_COLUMNS)-set(ORDERED_EVENTS_DF_COLUMNS))
# print(set(ORDERED_EVENTS_DF_COLUMNS)-set(EVENTS_DF_COLUMNS))
# 
# print(len(EVENTS_DF_COLUMNS)==len(ORDERED_EVENTS_DF_COLUMNS))
# print(len(SESSIONS_DF_COLUMNS)==len(ORDERED_SESSIONS_DF_COLUMNS))