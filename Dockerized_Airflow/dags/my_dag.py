from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime, timedelta


default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 11),
    'email': ['msbeni@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': True
}


def _my_func(ds):
    print(ds)


with DAG('my_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    my_task = PythonOperator(
        owner='msbeni',
        task_id='my_task_1',
        python_callable=_my_func,
        provide_context=True
    )

    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo '{{ ti.try_number }}' && exit 1"
    )

    my_task >> my_task_2

