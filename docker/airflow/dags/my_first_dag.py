from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import shutil
import random
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'simple_data_ingestion',
    default_args=default_args,
    description='A simple data ingestion DAG',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    def read_data(**context):
        raw_data_folder = 'C:/Users/salma elyagoubi/error418/raw_data'  
        files = os.listdir(raw_data_folder)
        selected_file = random.choice(files)
        return os.path.join(raw_data_folder, selected_file)

    def save_file(task_instance, **context):
        file_path = task_instance.xcom_pull(task_ids='read_data')
        good_data_folder = 'C:/Users/salma elyagoubi/error418/good_data'
        if not os.path.exists(good_data_folder):
            os.makedirs(good_data_folder)
        shutil.move(file_path, good_data_folder)

    read_data = PythonOperator(
        task_id='read_data',
        python_callable=read_data,
        provide_context=True,
    )

    # Define the 'save-file' task
    save_file = PythonOperator(
        task_id='save_file',
        python_callable=save_file,
        provide_context=True,
    )

    # Set the task sequence
    read_data >> save_file
