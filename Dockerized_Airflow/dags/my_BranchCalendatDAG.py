from airflow.models import DAG, Variable
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime
import yaml


def _check_holidays(ds):   # ds is the DAG Execution Date
    with open('dags/files/days_off.yml', 'r') as f:
        days_off = set(yaml.load(f, loader=yaml.FullLoader))
        if ds not in days_off:
            return 'process_data'
    return 'stop_processing'


with DAG('myBranchCalendarDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    check_holidays = BranchPythonOperator(
        task_id='check_holidays',
        python_callable=_check_holidays
    )
    process_data = DummyOperator(task_id='process_data')
    cleaning_data = DummyOperator(task_id='claening_data')
    stop_processing = DummyOperator(task_id='stop_processing')

    check_holidays >> [process_data, stop_processing]
    process_data  >> cleaning_data