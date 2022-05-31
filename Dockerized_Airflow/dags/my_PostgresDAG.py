from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator

from datetime import datetime


with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )

    store = PostgresOperator(
        task_id='store',
        postgres_conn_id='postgres',
        sql=[
            "sql/INSERT_INTO_MY_TABLE.sql",
            "SELECT * FROM my_table;"
            ],
        parameters={
          'filename': 'data.csv'
        }
    )