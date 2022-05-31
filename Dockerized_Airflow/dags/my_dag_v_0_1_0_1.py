# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from airflow.operators.bash import BashOperator
# from datetime import datetime, timedelta
# from airflow.utils.task_group import TaskGroup
#
#
# default_args = {
#     'owner': 'msbeni',
#     'start_date': datetime(2022, 5, 1),
#     'email': ['msbeni@gmail.com'],
#     'email_on_failure': False,
#     'email_on_retry': True
# }
#
#
# def _my_func(execution_date):
#     if execution_date.day == 5:
#         raise ValueError("Error")
#
#
# with DAG('my_dag_v0.0.2', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:
#
#     extract_a = BashOperator(
#         owner='msbeni',
#         task_id='extract_a',
#         bash_command="echo 'task 1' && sleep 10"
#     )
#
#     extract_b = BashOperator(
#         owner='msbeni',
#         task_id='extract_b',
#         bash_command="echo 'task 1' && sleep 10"
#     )
#
#     with TaskGroup(group_id='group1') as tg1:
#         process_a = BashOperator(
#             owner='mohasa',
#             task_id='process_a',
#             retries=3,
#             retry_exponential_backoff=True,
#             retry_delay=timedelta(seconds=10),
#             bash_command="echo '{{ ti.try_number }}' && sleep 20",
#             pool="concurrency_limitation_pool"
#         )
#
#         process_b = BashOperator(
#             owner='mohasa',
#             task_id='process_b',
#             retries=3,
#             retry_exponential_backoff=True,
#             retry_delay=timedelta(seconds=10),
#             bash_command="echo '{{ ti.try_number }}' && sleep 20",
#             pool="concurrency_limitation_pool"
#         )
#
#         process_c = BashOperator(
#             owner='mohasa',
#             task_id='process_c',
#             retries=3,
#             retry_exponential_backoff=True,
#             retry_delay=timedelta(seconds=10),
#             bash_command="echo '{{ ti.try_number }}' && sleep 20",
#             pool="concurrency_limitation_pool"
#         )
#
#         [process_a, process_b, process_c]
#
#     store = PythonOperator(
#         owner='msbeni',
#         task_id='store',
#         python_callable=_my_func,
#         depends_on_past=True
#     )
#
#     [extract_a, extract_b] >> tg1 >> store

