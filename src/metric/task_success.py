import numpy as np
import plt

from src.data.cwlog_parser import *

# parse log
sessions_df, events_df = parse_cwlog_all(csv_save=True)

# print(sessions_df.describe())
# print(events_df.describe())
#
# print(sessions_df.info())
# print(events_df.info())

# 1. Task Success Rate
task_success_df = sessions_df[['participantId','taskId','sessionId','startTime','endTime']]

task_success_df['task_completion_time'] = (task_success_df['endTime'] - task_success_df['startTime'])
task_success_df.loc[
    task_success_df['task_completion_time'] <= pd.Timedelta(minutes=7),
    'task_completion_point'
] = 1
task_success_df.loc[
    task_success_df['task_completion_time'] > pd.Timedelta(minutes=7),
    'task_completion_point'
] = 0

task_success_df['task_completion_time'] /= np.timedelta64(1, 's')

#
print(task_success_df.describe())
print(task_success_df.info())
print(task_success_df['task_completion_time'].value_counts())


plt.hist(task_success_df[task_success_df['taskId']=='Task_1']['task_completion_time'].to_list(), bins=5, label='Task 1')
plt.ylabel('Counts for Task Completion Time')
plt.xlabel('Task Completion Time (seconds)')
plt.legend()
plt.show()
plt.hist(task_success_df[task_success_df['taskId']=='Task_2']['task_completion_time'].to_list(), bins=5, label='Task 2')
plt.ylabel('Counts for Task Completion Time')
plt.xlabel('Task Completion Time (seconds)')
plt.legend()
plt.show()
plt.hist(task_success_df[task_success_df['taskId']=='Task_3']['task_completion_time'].to_list(), bins=5, label='Task 3')
plt.ylabel('Counts for Task Completion Time')
plt.xlabel('Task Completion Time (seconds)')
plt.legend()
plt.show()

task_points = [
    int(task_success_df[task_success_df['taskId']=='Task_1']['task_completion_point'].sum()),
    int(task_success_df[task_success_df['taskId']=='Task_2']['task_completion_point'].sum()),
    int(task_success_df[task_success_df['taskId']=='Task_3']['task_completion_point'].sum()),
]
task_success_rates = []

for i in range(3):
    task_success_rates.append(task_points[i]/len(task_success_df[task_success_df['taskId']==f'Task_{i+1}']))

print(f'Individual Task Success Point : {task_points}')
print(f'Individual Task Success Rate : {task_success_rates}')
print(f'Overall Task Success Rate : {sum(task_points)/len(task_success_df)}')