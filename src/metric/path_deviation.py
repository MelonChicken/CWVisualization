from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from src.config.config import LOG_PATH
from src.data.cwlog_parser import parse_cwlog_all


PATH_EVENT_TYPES = {"page_load", "back_navigation"}


def normalize_url(url: str | pd.NA) -> str | None:
    """
    이벤트 URL에서 경로 비교에 사용할 페이지 식별자를 추출한다.

    Args:
        url: 이벤트에 기록된 원본 URL 문자열.

    Returns:
        쿼리스트링의 `id` 값이 있으면 해당 값을 반환하고,
        없으면 path의 마지막 세그먼트를 반환한다.
        URL이 비어 있으면 None을 반환한다.
    """
    if pd.isna(url):
        return None

    parsed = urlparse(str(url))
    query = parse_qs(parsed.query)
    page_id = query.get("id", [None])[0]

    if page_id:
        return page_id
    if parsed.path:
        return parsed.path.rstrip("/").split("/")[-1]
    return None


def event_to_action(row: pd.Series) -> str | None:
    """
    단일 이벤트 레코드를 경로 비교용 action 문자열로 변환한다.

    Args:
        row: events_df의 한 행. 최소한 `type`, `url` 컬럼을 포함해야 한다.

    Returns:
        `back_navigation`은 `BACK`,
        `page_load`는 `LOAD:{page_id}` 형태로 변환한다.
        경로 계산과 무관한 이벤트는 None을 반환한다.
    """
    event_type = row["type"]

    if event_type == "back_navigation":
        return "BACK"

    if event_type == "page_load":
        page = normalize_url(row.get("url"))
        return f"LOAD:{page}" if page else None

    return None


def extract_action_sequence(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 이벤트 테이블에서 경로 계산에 필요한 행동열만 추출한다.

    Args:
        events_df: 원본 이벤트 데이터프레임.

    Returns:
        `page_load`, `back_navigation`만 남기고 시간순으로 정렬한 뒤
        `action` 컬럼을 추가한 데이터프레임을 반환한다.
    """
    action_df = events_df.loc[events_df["type"].isin(PATH_EVENT_TYPES)].copy()
    action_df = action_df.sort_values(["PID-TID", "timestampMs"]).reset_index(drop=True)
    action_df["action"] = action_df.apply(event_to_action, axis=1)
    action_df = action_df.loc[action_df["action"].notna()].copy()
    return action_df


def load_reference_paths(
    basic_path_dir: str | Path | None = None,
) -> dict[str, list[str]]:
    """
    BASIC PATH 로그에서 Task별 기준 경로를 자동으로 읽어온다.

    Args:
        basic_path_dir: BASIC PATH 로그가 저장된 디렉터리 경로.
            None이면 기본값으로 `res/log/BASIC PATH`를 사용한다.

    Returns:
        `{"Task_x": [action1, action2, ...]}` 형태의 기준 경로 사전.
    """
    basic_dir = Path(basic_path_dir) if basic_path_dir else LOG_PATH / "BASIC PATH"
    reference_paths: dict[str, list[str]] = {}

    for file_path in sorted(basic_dir.glob("*.json")):
        with open(file_path, "r", encoding="utf-8") as f:
            log = json.load(f)

        events_df = pd.json_normalize(log.get("events", []))
        if events_df.empty:
            continue

        events_df["participantId"] = log.get("participantId")
        events_df["taskId"] = log.get("taskId")
        events_df["PID-TID"] = (
            events_df["participantId"].astype("string")
            + "-"
            + events_df["taskId"].astype("string")
        )

        action_df = extract_action_sequence(events_df)
        if action_df.empty:
            continue

        reference_paths[str(action_df["taskId"].iloc[0])] = action_df["action"].tolist()

    return reference_paths


def count_repetitions(actions: list[str]) -> int:
    """
    행동열에서 연속으로 같은 action이 반복된 횟수를 계산한다.

    Args:
        actions: 세션별 action 문자열 리스트.

    Returns:
        바로 이전 action과 동일한 action이 나온 횟수의 합.
    """
    if not actions:
        return 0

    return sum(curr == prev for prev, curr in zip(actions, actions[1:]))


def compute_path_deviation(
    events_df: pd.DataFrame,
    reference_paths: dict[str, list[str]],
) -> pd.DataFrame:
    """
    세션별 Path Deviation Score를 계산한다.

    Args:
        events_df: 전체 이벤트 데이터프레임.
        reference_paths: Task별 기준 경로 사전.

    Returns:
        세션별 실제 경로, 기준 경로, 뒤로가기 횟수(`B_s`),
        반복 횟수(`Rep_s`), 추가 행동 수, 최종 `path_deviation_score`
        를 담은 데이터프레임.
    """
    action_df = extract_action_sequence(events_df)
    rows: list[dict] = []

    for pid_tid, group in action_df.groupby("PID-TID", sort=False):
        actions = group["action"].tolist()
        task_id = group["taskId"].iloc[0]
        reference = reference_paths.get(task_id, [])

        back_count = int((group["type"] == "back_navigation").sum())
        repetition_count = count_repetitions(actions)
        extra_action_count = max(0, len(actions) - len(reference))

        rows.append(
            {
                "PID-TID": pid_tid,
                "participantId": group["participantId"].iloc[0],
                "taskId": task_id,
                "actual_path": actions,
                "reference_path": reference,
                "actual_len": len(actions),
                "reference_len": len(reference),
                "B_s": back_count,
                "Rep_s": repetition_count,
                "extra_actions": extra_action_count,
                "path_deviation_score": back_count + repetition_count + extra_action_count,
            }
        )

    return pd.DataFrame(rows).sort_values(["taskId", "participantId"]).reset_index(drop=True)


def summarize_path_deviation(path_deviation_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Path Deviation Score의 전체 평균과 Task별 요약 통계를 계산한다.

    Args:
        path_deviation_df: `compute_path_deviation` 결과 데이터프레임.

    Returns:
        전체 요약 1행 데이터프레임과 Task별 요약 데이터프레임 튜플.
    """
    overall_summary_df = pd.DataFrame(
        [
            {
                "session_count": len(path_deviation_df),
                "mean_pds": path_deviation_df["path_deviation_score"].mean(),
                "median_pds": path_deviation_df["path_deviation_score"].median(),
                "mean_B_s": path_deviation_df["B_s"].mean(),
                "mean_Rep_s": path_deviation_df["Rep_s"].mean(),
                "mean_extra_actions": path_deviation_df["extra_actions"].mean(),
            }
        ]
    )

    task_summary_df = (
        path_deviation_df.groupby("taskId", as_index=False)
        .agg(
            session_count=("PID-TID", "count"),
            mean_pds=("path_deviation_score", "mean"),
            median_pds=("path_deviation_score", "median"),
            mean_B_s=("B_s", "mean"),
            mean_Rep_s=("Rep_s", "mean"),
            mean_extra_actions=("extra_actions", "mean"),
        )
        .sort_values("taskId")
        .reset_index(drop=True)
    )

    return overall_summary_df, task_summary_df


if __name__ == "__main__":
    _, events_df = parse_cwlog_all(csv_save=False)
    reference_paths = load_reference_paths()

    print("reference_paths =", reference_paths)
    path_deviation_df = compute_path_deviation(events_df, reference_paths)
    overall_summary_df, task_summary_df = summarize_path_deviation(path_deviation_df)

    print("\n[Session Scores]")
    print(path_deviation_df[["PID-TID", "taskId", "B_s", "Rep_s", "extra_actions", "path_deviation_score"]])
    print("\n[Overall Summary]")
    print(overall_summary_df)
    overall_summary_df.to_excel("path_deviation.xlsx")
    print("\n[Task Summary]")
    print(task_summary_df)
    task_summary_df.to_excel("task_summary.xlsx")
