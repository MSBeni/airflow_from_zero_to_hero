from airflow.models import DAG, Variable
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


@task(task_id="dec_task_1")
def process(func_vars):
    context = get_current_context()
    print(f"{func_vars['path']}/{func_vars['file_name']} - {context['ds']}")


with DAG('pyDAGdec', schedule_interval='@daily', start_date=datetime(2022, 5, 13), catchup=False) as dag:

    store = BashOperator(
        task_id="store",
        bash_command="echo 'store is called'"
    )

    process(Variable.get("vars_json", deserialize_json=True)) >> store