from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import shutil
import random
import os
import logging

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'simple_data_ingestion',
    default_args=default_args,
    description='A simple data ingestion DAG',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

def read_data(**context):
    raw_data_folder = Variable.get("raw_data_folder", default_var="C:/Users/salma elyagoubi/error418/raw_data")
    try:
        files = os.listdir(raw_data_folder)
        if not files:
            raise FileNotFoundError("No files found in the raw_data_folder.")
        selected_file = random.choice(files)
        selected_file_path = os.path.join(raw_data_folder, selected_file)
        logging.info(f"Selected file: {selected_file_path}")
        return selected_file_path
    except Exception as e:
        logging.error(f"Error reading data: {e}")
        raise

def save_file(task_instance, **context):
    file_path = task_instance.xcom_pull(task_ids='read_data')
    good_data_folder = Variable.get("good_data_folder", default_var="C:/Users/salma elyagoubi/error418/good_data")
    
    try:
        if not os.path.exists(good_data_folder):
            os.makedirs(good_data_folder)
        shutil.move(file_path, good_data_folder)
        logging.info(f"File moved to {good_data_folder}: {file_path}")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        raise

read_data_task = PythonOperator(
    task_id='read_data',
    python_callable=read_data,
    provide_context=True,
    dag=dag,
)

save_file_task = PythonOperator(
    task_id='save_file',
    python_callable=save_file,
    provide_context=True,
    dag=dag,
)

read_data_task >> save_file_task

