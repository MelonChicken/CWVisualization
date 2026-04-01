from src.config.config import *
from src.data.cwlog_parser import *

experiment_logs = []

for file_path in LOG_PATH.iterdir():
    # 확장자 확인
    if file_path.suffix == '.json':
        experiment_logs.append(parse_cwlog(file_path))

len(experiment_logs)
