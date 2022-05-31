from airflow.models import DAG
from airflow.operators.datetime import BranchDateTimeOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime, time

with DAG('myBranchDateTimeDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    is_in_time_frame = BranchDateTimeOperator(
        task_id='is_in_time_frame',
        follow_task_ids_if_true=['move_forward'],
        follow_task_ids_if_false=['end_dag'],
        target_lower=time(10, 0, 0),
        target_upper=time(11, 0, 0),
        use_task_execution_date=True
    )

    move_forward = DummyOperator(task_id='move_forward')
    end_dag = DummyOperator(task_id='end_dag')

    is_in_time_frame >> [move_forward, end_dag]
