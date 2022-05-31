from airflow.models import DAG, Variable
from airflow.operators.bash import BashOperator

from datetime import datetime


with DAG('myBashDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh",
        do_xcom_push=False,
        env={
          "api_aws":"{{ var.value.api_key_aws }}"
        }
    )

