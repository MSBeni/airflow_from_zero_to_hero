from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.sensors.file_sensor import FileSensor

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2019, 12, 24),
}

with DAG("trigger_rules", default_args=default_args, schedule_interval=timedelta(1)) as dag:

    t1 = BashOperator(task_id="print_date", bash_command="date")

    t2 = BashOperator(task_id="sleep", bash_command="sleep 5")

    t3 = FileSensor(
    	task_id="check_file_exists",
        filepath="/usr/local/airflow/dags/test.py",
        fs_conn_id="fs_default",
    	poke_interval= 5,
    	timeout=5
    )

    t4 = BashOperator(
        task_id='final_task',
        bash_command='echo DONE!',
        trigger_rule='all_done'
    )

    [t1, t2, t3] >> t4
