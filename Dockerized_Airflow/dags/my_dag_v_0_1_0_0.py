from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 1),
    'email': ['msbeni@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': True
}


def _my_func(execution_date):
    if execution_date.day == 5:
        raise ValueError("Error")


with DAG('my_dag_v0.0.1', schedule_interval='@daily', default_args=default_args, catchup=True) as dag:

    my_task_1 = BashOperator(
        owner='msbeni',
        task_id='my_task_1',
        bash_command="echo 'task 1' && sleep 10"
    )

    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo '{{ ti.try_number }}' && exit 0"
    )

    my_task_3 = PythonOperator(
        owner='msbeni',
        task_id='my_task_3',
        python_callable=_my_func,
        depends_on_past=True
    )

    my_task_1 >> my_task_2 >> my_task_3

