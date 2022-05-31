# https://api.nationalize.io?name=nathaniel

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import json

from datetime import datetime, timedelta
import pandas as pd
import requests

default_args = {
    'owner': 'msbeni',
    'email': ['msb@gg.com'],
    'start_date': datetime(2022, 5, 15),
    'retries': 3,
    'email_on_retry': False,
    'email_on_failure': False
}


# @task(task_id='extract_raw_data')
def _extarct_raw_data():
    api_req = requests.get('https://api.nationalize.io?name=nathaniel')
    data = api_req.json()
    print(data)
    with open('dags/data/nationalize_data/nationalize_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return 'dags/data/nationalize_data/'


def _load_raw_data():
    data = json.loads(open('dags/data/nationalize_data/nationalize_data.json', 'r').read())
    _name = data['name']
    cnt_id, probability, name = list(), list(), list()
    for el in data['country']:
        name.append(_name)
        cnt_id.append(el['country_id'])
        probability.append(el['probability'])

    df = pd.DataFrame()
    cols = ['name', 'country_id', 'probability']
    data = [name, cnt_id, probability]
    for i in range(len(cols)):
        df[cols[i]] = data[i]
    df.to_csv('dags/data/nationalize_data/'+_name+'.csv')
    return _name


def _read_clean_data_to_load(ti):
    returned_vals = ti.xcom_pull(task_ids=['extract_raw_data', 'transform_loaded_data'])
    data_file_name = returned_vals[0] + returned_vals[1] + '.csv'
    df = pd.read_csv(data_file_name)
    print(df)


with DAG('nationalize_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    create_folder_nationalize_data = BashOperator(
        task_id='create_folder_nationalize_data',
        bash_command='cd /opt/airflow/dags/data/ && mkdir -p nationalize_data',
        do_xcom_push=False,
        trigger_rule='all_done'
    )

    extract_raw_data = PythonOperator(
        task_id='extract_raw_data',
        python_callable=_extarct_raw_data,
        retries=3,
        retry_delay=timedelta(seconds=10),
        retry_exponential_backoff=True,
    )

    transform_loaded_data = PythonOperator(
        task_id='transform_loaded_data',
        python_callable=_load_raw_data
    )

    load_data_to_gcp = PythonOperator(
        task_id='load_data_to_gcp',
        python_callable=_read_clean_data_to_load
    )

    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')

    start >> create_folder_nationalize_data >> extract_raw_data >> transform_loaded_data >> load_data_to_gcp >> end