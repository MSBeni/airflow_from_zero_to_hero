from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task

from datetime import datetime


# @task(task_id='pyxcom')
# def _check_vars_2(**context):
#     val = str(context['execution_date'])
#     return val


def _check_vars(**context):
    # print(context['execution_date'])
    val = str(context['execution_date'])
    return val


def _get_vars(**kwargs):
    print(kwargs['push_data'])
    return kwargs['push_data']


def _getter_new(ti):
    date = ti.xcom_pull(task_ids='xcom_task_2')
    print(date)


with DAG('xcom_checker', schedule_interval=None, start_date=datetime(2022, 5, 15), catchup=False) as dag:

    xcom_task_1 = PythonOperator(
        task_id='xcom_task_1',
        python_callable=_check_vars
    )

    xcom_task_2 = PythonOperator(
        task_id='xcom_task_2',
        python_callable=_get_vars,
        op_kwargs={'push_data': "{{ ti.xcom_pull(task_ids='xcom_task_1') }}"}
    )

    xcom_task_3 = PythonOperator(
        task_id='xcom_task_3',
        python_callable=_getter_new,
    )

    xcom_task_1 >> xcom_task_2 >> xcom_task_3