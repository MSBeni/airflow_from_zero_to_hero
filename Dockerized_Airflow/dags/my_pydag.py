from airflow.models import DAG, Variable
from airflow.operators.python import PythonOperator

from datetime import datetime

default_arguments = {
    'start_date': datetime(2022, 5, 13),
    'owner': 'msbeni',
    'email': ''
}


def _task_1(file_path, file_name):
    print(f"{file_path}/{file_name}")


def _task_2(**kwargs):
    print(f"{kwargs['file_path']}/{kwargs['file_name']}")


def _task_3(**kwargs):
    print(f"{kwargs['file_path']}/{kwargs['file_name']}")


def _task_4(**kwargs):
    print(f"{kwargs['path']}/{kwargs['file_name']} - {kwargs['ds']}")


with DAG('pyDAG', schedule_interval='@daily', default_args=default_arguments, catchup=False) as dag:

    pyDag_task_1 = PythonOperator(
        task_id='pyDag_task_1',
        owner='mohasa',
        python_callable=_task_1,
        op_args=['/usr/local/airflow', 'data.csv']
    )

    pyDag_task_2 = PythonOperator(
        task_id='pyDag_task_2',
        owner='mohasa',
        python_callable=_task_2,
        op_kwargs={'file_path': '/usr/local/airflow', 'file_name':'data.csv'}
    )

    pyDag_task_3 = PythonOperator(
        task_id='pyDag_task_3',
        owner='mohasa',
        python_callable=_task_3,
        op_kwargs={'file_path': '{{ var.value.path }}', 'file_name':'{{ var.value.file_name }}'}
    )

    pyDag_task_4 = PythonOperator(
        task_id='pyDag_task_4',
        owner='mohasa',
        python_callable=_task_4,
        op_kwargs=Variable.get("vars_json", deserialize_json=True)
    )

    pyDag_task_1 >> pyDag_task_2 >> pyDag_task_3

