import asyncio
import os
import pandas as pd
import random
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import great_expectations as ge
import json
import requests
from datetime import datetime
from great_expectations.dataset.pandas_dataset import PandasDataset
from great_expectations.data_context.data_context import DataContext
from airflow.operators.python import BranchPythonOperator
import asyncpg

DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = 'salma'
DB_HOST = 'host.docker.internal'
DB_PORT = 5432

dag_folder = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(dag_folder, 'raw-data')
good_data_path = os.path.join(dag_folder, 'good-data')
bad_data_path = os.path.join(dag_folder, 'bad-data')
ge_directory = os.path.abspath(os.path.join(dag_folder, '..', 'gx'))

def read_data(**kwargs):
    files = [file for file in os.listdir(RAW_DATA_PATH) if file.endswith('.csv')]
    if not files:
        raise FileNotFoundError("No CSV files found in directory.")
    selected_file = random.choice(files)
    file_path = os.path.join(RAW_DATA_PATH, selected_file)
    print("file_path in read_data is ", file_path)
    kwargs["ti"].xcom_push(key="file_path", value=file_path)

def read_and_prepare_data(file_path):
    # Read the CSV without specifying data types to handle 'INVALID' strings
    df = pd.read_csv(file_path, dtype=str)

    # Attempt to convert columns to appropriate data types
    for col in df.columns:
        if col != 'Potability':  # Potability should be an integer
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

def send_alerts(**kwargs):
    # Pulling validation results from XCom
    validation_results = kwargs["ti"].xcom_pull(key="validation_results", task_ids="validate_data")
    if isinstance(validation_results, str):
        validation_results = json.loads(validation_results)  # Convert the JSON string to a dictionary

    print("validation_results in send_alerts is ", validation_results)

    run_id = kwargs["ti"].xcom_pull(key="run_id", task_ids="validate_data")
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    df = pd.read_csv(file_path)

    # Extracting failed expectations
    failed_expectations = [
        result for result in validation_results["results"] if not result["success"]
    ]

    total_failed_count = len(failed_expectations)

    error_summary = os.linesep.join([
        f"- Expectation {index + 1} on column '{expectation['expectation_config']['kwargs']['column']}': " +
        f"{expectation['expectation_config']['expectation_type']} failed with " +
        f"{expectation['result'].get('unexpected_count', 0)} unexpected values."
        for index, expectation in enumerate(failed_expectations)
    ])
    
    teams_webhook_url = "https://epitafr.webhook.office.com/webhookb2/5ce4c8bd-0c04-44c6-9197-767b65a4e4c6@3534b3d7-316c-4bc9-9ede-605c860f49d2/IncomingWebhook/d7cab1faf1ee4d4697a0fbe011a24f4d/b873876a-670d-432b-9b74-e876608938b0"
    headers = {"Content-Type": "application/json"}
    bad_rows_indices = set()

    # Process each result to find failed expectations and their indices
    for result in validation_results["results"]:
        if not result["success"]:
            if (
                "partial_unexpected_list" in result["result"]
                and result["result"]["partial_unexpected_list"]
            ):
                # Assume partial_unexpected_list contains the row indices (this might need adjustment based on actual data structure)
                for value in result["result"]["partial_unexpected_list"]:
                    # Find all occurrences of this unexpected value in the specified column
                    index_list = df.index[
                        df[result["expectation_config"]["kwargs"]["column"]] == value
                    ].tolist()
                    bad_rows_indices.update(index_list)
                    
    bad_rows_indices_len = len(bad_rows_indices)
    kwargs["ti"].xcom_push(key="bad_rows_indices_len", value=bad_rows_indices_len)
    if bad_rows_indices_len > 3:
        criticality = "high"
    elif bad_rows_indices_len > 2:
        criticality = "medium"
    else:
        criticality = "low"

    kwargs["ti"].xcom_push(key="criticality", value=criticality)
    alert_message = {
        "text": (
            f"Data Problem Alert\n"
            f"Run ID: {run_id}\n"
            f"File Path: {file_path}\n\n"
            f"Criticality: {criticality}\n"
            f"Number of Failed Rows: {len(bad_rows_indices)}\n\n"
            f"Summary: {total_failed_count} expectations failed validation.\n\n"
            f"Error Details:\n"
            f"{error_summary}"
        )
    }
    print("alert_message is", alert_message)

    try:
        response = requests.post(teams_webhook_url, headers=headers, json=alert_message)
        if response.status_code == 200:
            print("Alert sent to Teams successfully.")
        else:
            print(f"Failed to send alert to Teams. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending alert to Teams: {e}")

def validate_data(**kwargs):
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    print("file_path in validate_data is ", file_path)
    data_asset_name = os.path.basename(file_path).split(".")[0]
    print("data_asset_name is ", data_asset_name)

    df = read_and_prepare_data(file_path)
    print("Data types after reading CSV:\n", df.dtypes)

    ge_directory = os.path.abspath(os.path.join(dag_folder, '..', 'gx'))
    context = DataContext(context_root_dir=ge_directory)
    expectation_suite_name = "ex_dyali"
    expectation_suite = context.get_expectation_suite(expectation_suite_name)

    ge_df = PandasDataset(df)
    ge_df._initialize_expectations(expectation_suite)
    validation_results = ge_df.validate()
    print('validation_results:', validation_results)

    # Convert validation results to JSON serializable dictionary
    validation_results_dict = validation_results.to_json_dict()

    run_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kwargs["ti"].xcom_push(key="validation_results", value=json.dumps(validation_results_dict))
    kwargs["ti"].xcom_push(key="run_id", value=run_id)

    if validation_results["success"]:
        print(file_path, "is good data")
        kwargs["ti"].xcom_push(key="data_quality", value="good_data")
    else:
        print(file_path, "is bad data")
        kwargs["ti"].xcom_push(key="data_quality", value="bad_data")
        bad_file_path = os.path.join(bad_data_path, os.path.basename(file_path))
        df.to_csv(bad_file_path, index=False)
        print(f"Bad data saved at {bad_file_path}")
        
def decide_which_path(**kwargs):
    ti = kwargs["ti"]
    data_quality = ti.xcom_pull(task_ids="validate_data", key="data_quality")
    if data_quality == "good_data":
        return "save_file"
    else:
        return ["send_alerts", "save_data_errors", "save_file"]

def save_file(**kwargs):
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    validation_results_json = kwargs["ti"].xcom_pull(key="validation_results", task_ids="validate_data")
    
    validation_results = json.loads(validation_results_json)
    
    df = pd.read_csv(file_path)
    bad_rows_indices = set()

    for result in validation_results["results"]:
        if not result["success"]:
            if (
                "partial_unexpected_list" in result["result"]
                and result["result"]["partial_unexpected_list"]
            ):
                for value in result["result"]["partial_unexpected_list"]:
                    index_list = df.index[
                        df[result["expectation_config"]["kwargs"]["column"]] == value
                    ].tolist()
                    bad_rows_indices.update(index_list)

    df_bad = df.iloc[list(bad_rows_indices)]
    df_good = df.drop(index=list(bad_rows_indices))

    os.makedirs(good_data_path, exist_ok=True)
    os.makedirs(bad_data_path, exist_ok=True)

    good_file_path = os.path.join(good_data_path, os.path.basename(file_path))
    bad_file_path = os.path.join(bad_data_path, os.path.basename(file_path))

    if not df_good.empty:
        df_good.to_csv(good_file_path, index=False)
        print(f"Saved good data to {good_file_path}")

    if not df_bad.empty:
        df_bad.to_csv(bad_file_path, index=False)
        print(f"Saved bad data to {bad_file_path}")

    os.remove(file_path)

async def create_db_connection():
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Database connection established.")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

async def close_db_connection(conn):
    await conn.close()
    print("Database connection closed.")

async def save_data_errors_async(ti):
    conn = await create_db_connection()
    try:
        async with conn.transaction():
            exists = await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}')")
            if not exists:
                await conn.execute(f'CREATE DATABASE {DB_NAME}')
                print(f"Database '{DB_NAME}' created successfully.")
            else:
                print(f"Database '{DB_NAME}' already exists.")
                
        create_table_result = await conn.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_statistics (
                id SERIAL PRIMARY KEY,
                total_rows INTEGER,
                failed_rows INTEGER,
                timestamp TIMESTAMP,
                file_path VARCHAR(500),
                criticality VARCHAR(500),
                error_details JSON
            );
        """)
        print("Create table result:", create_table_result)

        file_path = ti.xcom_pull(key="file_path", task_ids="read_data")
        validation_results = ti.xcom_pull(key="validation_results", task_ids="validate_data")

        # Deserialize validation_results if it's a string
        if isinstance(validation_results, str):
            validation_results = json.loads(validation_results)

        print("🚀 ~ validation_results:", validation_results["results"])
        file_path = ti.xcom_pull(key="file_path", task_ids="read_data")
        print("🚀 ~ file_path:", file_path)
        failed_expectations = [
            result for result in validation_results["results"] if not result["success"]
        ]
        print("🚀 ~ failed_expectations:", failed_expectations)
        error_summary_json = {
            "error_details": [
                {
                    "expectation_number": index + 1,
                    "column": expectation['expectation_config']['kwargs']['column'],
                    "expectation_type": expectation['expectation_config']['expectation_type'],
                    "unexpected_count": expectation['result'].get('unexpected_count', 0),
                    "unexpected_values": expectation['result'].get('partial_unexpected_list', [])
                }
                for index, expectation in enumerate(failed_expectations)
            ]
        }
        print("Error summary:", error_summary_json)
        total_rows = len(validation_results["results"])
        
        criticality = ti.xcom_pull(key="criticality", task_ids="send_alerts")
        bad_rows_indices_len = ti.xcom_pull(key="bad_rows_indices_len", task_ids="send_alerts")
        insert_result = await conn.execute(
            """
            INSERT INTO data_quality_statistics (
                total_rows, failed_rows, timestamp, file_path, criticality, error_details
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            total_rows,
            bad_rows_indices_len,
            datetime.now(),
            file_path,
            criticality,
            json.dumps(error_summary_json)
        )
        print("Insert result:", insert_result)
        print("Data quality statistics saved to the database.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await close_db_connection(conn)

def save_data_errors(**kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(save_data_errors_async(kwargs['ti']))

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

dag = DAG(
    "ingestion dag",
    default_args=default_args,
   schedule_interval="*/2 * * * *",
    start_date=days_ago(1),
    catchup=False
)

read_data_task = PythonOperator(
    task_id="read_data",
    python_callable=read_data,
    provide_context=True,
    dag=dag,
)

validate_data_task = PythonOperator(
    task_id="validate_data",
    python_callable=validate_data,
    dag=dag,
)

branch_task = BranchPythonOperator(
    task_id="branch_based_on_validation",
    python_callable=decide_which_path,
    provide_context=True,
    dag=dag,
)

send_alerts_task = PythonOperator(
    task_id="send_alerts",
    python_callable=send_alerts,
    provide_context=True,
    dag=dag,
    trigger_rule="all_success",
)

save_file_task = PythonOperator(
    task_id="save_file",
    python_callable=save_file,
    provide_context=True,
    dag=dag,
)

save_data_errors_task = PythonOperator(
    task_id="save_data_errors",
    python_callable=save_data_errors,
    provide_context=True,
    dag=dag,
    trigger_rule="all_success",
)

read_data_task >> validate_data_task >> branch_task
branch_task >> save_file_task
branch_task >> send_alerts_task
branch_task >> save_data_errors_task