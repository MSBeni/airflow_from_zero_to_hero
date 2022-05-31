from airflow.models import DAG, Variable
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime
import requests


default_args = {
    'start_date': datetime(2022, 5, 15)
}


def _read_data():
    headers = {'x-rapidapi-host': "imdb8.p.rapidapi.com",
               'x-rapidapi-key': "f435848c5fmshcd2f5e968553e49p1891f9jsn79a0bededf94"}
    url = "https://imdb8.p.rapidapi.com/auto-complete"
    data = requests.get(url,
                        headers=headers)

    print(data)


with DAG('url_checker', schedule_interval=None, default_args=default_args, catchup=False) as dag:

    read_date_task = PythonOperator(
        task_id='read_date_task',
        python_callable=_read_data
    )
