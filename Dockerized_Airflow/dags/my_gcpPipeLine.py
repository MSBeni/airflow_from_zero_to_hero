from airflow.models import DAG, Variable
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from airflow.operators.dummy import DummyOperator
from airflow.models.baseoperator import chain
from google.oauth2 import service_account

import requests
from datetime import datetime, timedelta
import pandas as pd

"""
Please create the following Variables in your local airflow server:
service_account_json_path: the_path_to_your_local_service_account
table_id: your_cgp_table_id
file_path_txt: path_to_local_initial_txt_file   --> This is used in initial table creation
"""

local_path = 'dags/data'
# service_account_json is airflow service_account_json_path variable

default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 15)
}


def _path_definition(ti):
    data = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    js_data = data.json()
    price_date = js_data['time']['updated']   # "May 15, 2022 16:29:00 UTC"
    newDate = datetime.strptime(price_date, '%b %d, %Y %H:%M:%S %Z')
    print(newDate.date())
    # ti.xcom_push(key='date', value=newDate.date())
    return str(newDate.date())


def _extract_from_api(**kwargs):
    data = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    js_data = data.json()
    price_date = js_data['time']['updated']   # "May 15, 2022 16:29:00 UTC"
    newDate = datetime.strptime(price_date, '%b %d, %Y %H:%M:%S %Z')
    coin_name = js_data['chartName']
    usd_price = float(''.join([el for el in js_data['bpi']['USD']['rate'] if el != ',']))
    gbp_price = float(''.join([el for el in js_data['bpi']['GBP']['rate'] if el != ',']))
    euro_price = float(''.join([el for el in js_data['bpi']['EUR']['rate'] if el != ',']))
    df = pd.DataFrame()
    columns = ['timestamp', 'coin_name', 'usd_price', 'gbp_price', 'euro_price']
    values = [[price_date], [coin_name], [usd_price], [gbp_price], [euro_price]]
    for i in range(len(columns)):
        df[columns[i]] = values[i]
    df.to_csv(kwargs['path']+'/'+str(newDate.date())+'/'+'bitcoin_price.csv')
    return kwargs['path']+'/'+str(newDate.date())+'/'+'bitcoin_price.csv'


def _create_table_on_gcp_database(**kwargs):
    """
    This function is called in a task in your DAG anc check if the table is already built do nothing otherwise create
    a table
    :param kwargs:
    :return:
    """
    client = bigquery.Client.from_service_account_json(kwargs['service_account_path'])
    try:
        client.get_table(kwargs['table_id'])  # Make an API request.
        print("Table {} already exists.".format(kwargs['table_id']))
    except NotFound:
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("coin_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("usd_price", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("gbp_price", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("euro_price", "FLOAT", mode="NULLABLE")
            ],
            source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1
        )

        source_file = open(kwargs['file_path_txt'], 'rb')

        job = client.load_table_from_file(source_file, kwargs['table_id'], job_config=job_config)

        print(job.result())


def _push_to_gcp(**kwargs):
    client = bigquery.Client.from_service_account_json(kwargs['service_account_path'])
    rows_to_insert = []
    df = pd.read_csv(kwargs['data_csv_saved_path'])
    for i in range(len(df.timestamp)):
        row_to_insert_ = {u"timestamp": df['timestamp'][i],
                          u"coin_name": df['coin_name'][i],
                          u"usd_price": df['usd_price'][i],
                          u"gbp_price": df['gbp_price'][i],
                          u"euro_price": df['euro_price'][i]}
        if row_to_insert_ not in rows_to_insert:
            rows_to_insert.append(row_to_insert_)

    errors = client.insert_rows_json(kwargs['table_id'], rows_to_insert)  # Make an API request.
    if not errors:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))


def _check_new_data_bigquery(**kwargs):
    credentials = service_account.Credentials.from_service_account_file(kwargs['service_account_path'], scopes=[
        "https://www.googleapis.com/auth/cloud-platform"])
    query = """SELECT COUNT(*) from {}""".format(kwargs['table_id'])
    df = pd.read_gbq(query, dialect='standard', credentials=credentials)
    print(df)


with DAG('GCPetlDAG', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    create_path = PythonOperator(
        task_id='create_path',
        python_callable=_path_definition
        # op_kwargs={'path': '{{ var.value.csv_path }}'}
    )

    mkdir_hourly_op = BashOperator(
        task_id='mkdir_hourly_op',
        bash_command="cd /opt/airflow/dags/data/ && mkdir -p '{{ ti.xcom_pull(task_ids='create_path') }}'",
        do_xcom_push=False
        # bash_command="scripts/make_directory.sh"
    )

    extract_data = PythonOperator(
        task_id='extract_data',
        python_callable=_extract_from_api,
        op_kwargs={'path': local_path}
        # op_kwargs={'path': '{{ var.value.csv_path }}'}
    )

    create_bq_table = PythonOperator(
        task_id='create_bq_table',
        python_callable=_create_table_on_gcp_database,
        op_kwargs={
            'service_account_path': '{{ var.value.service_account_json_path }}',
            'table_id': '{{ var.value.table_id }}',
            'file_path_txt': '{{ var.value.file_path_txt }}'
        }
    )

    wait_for_table_creation_task = BashOperator(
        task_id='wait_for_table_creation_task',
        bash_command="echo 'wait for table to be created on GCP' && sleep 10",
    )

    push_data_to_gcp = PythonOperator(
        task_id='push_data_to_gcp',
        python_callable=_push_to_gcp,
        op_kwargs={
            'service_account_path': '{{ var.value.service_account_json_path }}',
            'table_id': '{{ var.value.table_id }}',
            'data_csv_saved_path': "{{ ti.xcom_pull(task_ids='extract_data') }}"
        },
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
    )

    check_data_loaded_in_gbq = PythonOperator(
        task_id='check_data_loaded_in_gbq',
        python_callable=_check_new_data_bigquery,
        op_kwargs={
            'service_account_path': '{{ var.value.service_account_json_path }}',
            'table_id': '{{ var.value.table_id }}',
            'data_csv_saved_path': "{{ ti.xcom_pull(task_ids='extract_data') }}"
        }
    )


    begin = DummyOperator(task_id="begin")
    end = DummyOperator(task_id="end")

    chain(begin, create_path, mkdir_hourly_op, extract_data, create_bq_table, wait_for_table_creation_task,
          push_data_to_gcp, check_data_loaded_in_gbq, end)