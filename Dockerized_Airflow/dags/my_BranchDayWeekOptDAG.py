from airflow.models import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.weekday import BranchDayOfWeekOperator
from airflow.utils.weekday import WeekDay

from datetime import datetime, time

with DAG('myBranchWeekDayDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    task_a_bdwo = DummyOperator(task_id='task_a_bdwo')
    task_b_bdwo = DummyOperator(task_id='task_b_bdwo')

    is_wednesday = BranchDayOfWeekOperator(
        task_id='is_wednesday',
        follow_task_ids_if_true=['task_c_bdwo'],
        follow_task_ids_if_false=['task_end'],
        week_day=WeekDay.WEDNESDAY,
        use_task_execution_day=True,
    )
    task_c_bdwo = DummyOperator(task_id='task_c_bdwo')
    task_end = DummyOperator(task_id='task_end')

    task_a_bdwo >> task_b_bdwo >> is_wednesday >> [task_c_bdwo, task_end]