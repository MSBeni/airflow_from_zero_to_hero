from airflow.models import DAG, Variable
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime

def _check_accuracy(ds):   # ds is the DAG Execution Date
    accuracy = 0.16
    if accuracy > 0.15:
        return ['accurate', 'top_accurate']
    return 'inaccurate'


with DAG('myBranchpyDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    training_ml = DummyOperator(task_id='training_ml')
    check_accuracy = BranchPythonOperator(
        task_id='check_accuracy',
        python_callable=_check_accuracy
    )
    accurate = DummyOperator(task_id='accurate')
    top_accurate = DummyOperator(task_id='top_accurate')

    inaccurate = DummyOperator(task_id='inaccurate')

    publish_ml = DummyOperator(task_id='publish_ml', trigger_rule='none_failed_or_skipped')

    training_ml >> check_accuracy >> [accurate, inaccurate, top_accurate] >> publish_ml