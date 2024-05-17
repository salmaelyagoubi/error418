from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pandas as pd
import random
import shutil
from great_expectations.dataset import PandasDataset

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

raw_data_path = r'C:\Users\salma elyagoubi\error418\raw-data'
good_data_path = r'C:\Users\salma elyagoubi\error418\good-data'
bad_data_path = r'C:\Users\salma elyagoubi\error418\bad-data'

def read_data():
    files = os.listdir(raw_data_path)
    selected_file = random.choice(files)
    return os.path.join(raw_data_path, selected_file)

def validate_data(file_path):
    df = pd.read_csv(file_path)
    data = PandasDataset(df)
    return data.expect_column_values_to_not_be_null("ph")

def send_alerts(file_path, validation_results):
    if not validation_results['success']:
        print(f"Alert: Data quality issue found in {file_path}")
    else:
        print(f"Data in {file_path} is clean")

def split_and_save_data(file_path, validation_results):
    df = pd.read_csv(file_path)
    good_df = df[df['ph'].notnull()]
    bad_df = df[df['ph'].isnull()]

    if not good_df.empty:
        good_df.to_csv(os.path.join(good_data_path, os.path.basename(file_path)), index=False)
    if not bad_df.empty:
        bad_df.to_csv(os.path.join(bad_data_path, os.path.basename(file_path)), index=False)

    os.remove(file_path)

def save_data_errors(validation_results):
    if not validation_results['success']:
        print("Saving data issues to the database")

with DAG(
    'data_ingestion',
    default_args=default_args,
    description='A simple data ingestion DAG',
    schedule_interval=timedelta(minutes=1),
    catchup=False,
) as dag:

    read_data_task = PythonOperator(
        task_id='read_data',
        python_callable=read_data,
    )

    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        op_args=['{{ ti.xcom_pull(task_ids="read_data") }}'],
    )

    send_alerts_task = PythonOperator(
        task_id='send_alerts',
        python_callable=send_alerts,
        op_args=['{{ ti.xcom_pull(task_ids="read_data") }}', '{{ ti.xcom_pull(task_ids="validate_data") }}'],
    )

    split_and_save_data_task = PythonOperator(
        task_id='split_and_save_data',
        python_callable=split_and_save_data,
        op_args=['{{ ti.xcom_pull(task_ids="read_data") }}', '{{ ti.xcom_pull(task_ids="validate_data") }}'],
    )

    save_data_errors_task = PythonOperator(
        task_id='save_data_errors',
        python_callable=save_data_errors,
        op_args=['{{ ti.xcom_pull(task_ids="validate_data") }}'],
    )

    read_data_task >> validate_data_task >> [send_alerts_task, split_and_save_data_task, save_data_errors_task]
