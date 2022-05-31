from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.sql import BranchSQLOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime

with DAG('myBranchSQLDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    branch_craete_table = PostgresOperator(
        task_id='branch_craete_table',
        sql='sql/CREATE_TABLE_PARTNERS.sql',
        postgres_conn_id='postgres',
    )

    branch_insert_into_table = PostgresOperator(
        task_id='branch_insert_into_table',
        sql='sql/INSERT_INTO_PRTNERS.sql',
        postgres_conn_id='postgres',
    )

    choose_next_task = BranchSQLOperator(
        task_id='choose_next_task',
        sql="SELECT COUNT(1) FROM partners WHERE partner_status=TRUE",
        follow_task_ids_if_true=['process_sql'],
        follow_task_ids_if_false=['notif_email', 'notif_slack'],
        conn_id='postgres',
    )

    process_sql = DummyOperator(task_id='process_sql')

    notif_email = DummyOperator(task_id='notif_email')


    notif_slack = DummyOperator(task_id='notif_slack')

    branch_craete_table >> branch_insert_into_table >> choose_next_task >> [process_sql, notif_email, notif_slack]

