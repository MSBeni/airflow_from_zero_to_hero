import os

from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

from google.cloud import storage
from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryDeleteDatasetOperator,
    BigQueryCreateEmptyTableOperator,
)
from airflow.providers.google.cloud.transfers.local_to_gcs import (
    LocalFilesystemToGCSOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
# from great_expectations_provider.operators.great_expectations import (
#     GreatExpectationsOperator,
# )
# from include.great_expectations.configs.bigquery_configs import (
#     bigquery_checkpoint_config,
# )

base_path = Path(__file__).parents[2]
data_file = os.path.join(
    base_path,
    "include",
    "sample_data/yellow_trip_data/yellow_tripdata_sample_2019-01.csv",
)
ge_root_dir = os.path.join(base_path, "include", "great_expectations")
# checkpoint_config = bigquery_checkpoint_config

# In a production DAG, the global variables below should be stored as Airflow
# or Environment variables.
# bq_dataset = "great_expectations_bigquery_example"
bq_dataset = "mybitcoindataset22"
bq_table = "bitcoin"
gcp_bucket = "my_bitcoin_daily_price"
gcp_data_dest = "data/bitcoin_price.csv"

# Please Consider Installing these Requierments on Pypy package
# airflow-provider-great-expectations==0.1.4
# requests==2.27.1
# pandas==1.4.2
# jinja2>=3.0
# mistune<2
# jinja2>=3.0


def _extract_from_api():
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
    
    print(df)
    print(df.columns)
    client = storage.Client()
    bucket = client.get_bucket(gcp_bucket)

    bucket.blob(gcp_data_dest).upload_from_string(df.to_csv(), 'text/csv')


with DAG(
    "gcp_etl_great_expectations.bigquery",
    description="Example DAG showcasing loading and data quality checking with BigQuery and Great Expectations.",
    schedule_interval=None,
    start_date=datetime(2022, 5, 15),
    catchup=False,
) as dag:
    """
    ### Simple EL Pipeline with Data Quality Checks Using BigQuery and Great Expectations

    Before running the DAG, set the following in an Airflow or Environment Variable:
    - key: gcp_project_id
      value: [gcp_project_id]
    Fully replacing [gcp_project_id] with the actual ID.

    Ensure you have a connection to GCP, using a role with access to BigQuery
    and the ability to create, modify, and delete datasets and tables.

    What makes this a simple data quality case is:
    1. Absolute ground truth: the local CSV file is considered perfect and immutable.
    2. No transformations or business logic.
    3. Exact values of data to quality check are known.
    """

    """
    #### BigQuery dataset creation
    Create the dataset to store the sample data tables.
    """
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset", dataset_id=bq_dataset
    )

    """
    #### Extract Data From API and Load it to GCS
    Extract and load to GCS Operation
    """
    extract_data_load_to_gcs = PythonOperator(
        task_id='extract_data_load_to_gcs',
        python_callable=_extract_from_api
    )

    # """
    # #### Upload taxi data to GCS
    # Upload the test data to GCS so it can be transferred to BigQuery.
    # """
    # upload_bitcoin_data = LocalFilesystemToGCSOperator(
    #     task_id="upload_bitcoin_data",
    #     src=data_file,
    #     dst=gcp_data_dest,
    #     bucket=gcp_bucket,
    # )
    #
    # """
    # #### Create Temp Table for GE in BigQuery
    # """
    create_temp_table = BigQueryCreateEmptyTableOperator(
        task_id="create_temp_table",
        dataset_id=bq_dataset,
        table_id=f"{bq_table}_temp",
        schema_fields=[
            {"name": "idx", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "timestamp", "type": "STRING", "mode": "REQUIRED"},
            {"name": "coin_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "usd_price", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "gbp_price", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "euro_price", "type": "FLOAT", "mode": "NULLABLE"}
        ],
    )
    #
    # """
    # #### Transfer data from GCS to BigQuery
    # Moves the data uploaded to GCS in the previous step to BigQuery, where
    # Great Expectations can run a test suite against it.
    # """
    transfer_bitcoin_data = GCSToBigQueryOperator(
        task_id="bitcoin_data_gcs_to_bigquery",
        bucket=gcp_bucket,
        source_objects=[gcp_data_dest],
        skip_leading_rows=1,
        destination_project_dataset_table="{}.{}".format(bq_dataset, bq_table),
        schema_fields=[
            {"name": "idx", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "timestamp", "type": "STRING", "mode": "REQUIRED"},
            {"name": "coin_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "usd_price", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "gbp_price", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "euro_price", "type": "FLOAT", "mode": "NULLABLE"}
        ],
        source_format="CSV",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
        allow_jagged_rows=True,
    )
    #
    # """
    # #### Great Expectations suite
    # Run the Great Expectations suite on the table.
    # """
    # ge_bigquery_validation = GreatExpectationsOperator(
    #     task_id="ge_bigquery_validation",
    #     data_context_root_dir=ge_root_dir,
    #     checkpoint_config=checkpoint_config,
    # )
    #
    # """
    # #### Delete test dataset and table
    # Clean up the dataset and table created for the example.
    # """
    # delete_dataset = BigQueryDeleteDatasetOperator(
    #     task_id="delete_dataset",
    #     project_id="{{ var.value.gcp_project_id }}",
    #     dataset_id=bq_dataset,
    #     delete_contents=True,
    # )

    begin = DummyOperator(task_id="begin")
    end = DummyOperator(task_id="end")

    chain(
        begin,
        create_dataset,
        extract_data_load_to_gcs,
        create_temp_table,
        # upload_taxi_data,
        transfer_bitcoin_data,
        # ge_bigquery_validation,
        # delete_dataset,
        end,
    )
