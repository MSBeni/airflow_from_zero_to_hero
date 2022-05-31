from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator

from datetime import datetime


class CustomPostgresOperator(PostgresOperator):
    template_fields = ('sql', 'parameters')


def _my_task():
    return 'tweets.csv'


with DAG('myCustomPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    custom_create_table = PostgresOperator(
        task_id='custom_create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )

    my_psql_task = PythonOperator(
        task_id='my_psql_task',
        python_callable=_my_task
    )

    custom_store = CustomPostgresOperator(
        task_id='custom_store',
        postgres_conn_id='postgres',
        sql=[
            "sql/INSERT_INTO_MY_TABLE.sql",
            "SELECT * FROM my_table;"
            ],
        parameters={
          'filename': '{{ ti.xcom_pull(task_ids=["my_psql_task"]) }}'
        }
    )