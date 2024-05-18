
# Error418: Water Quality Analysis and Prediction

This project focuses on analyzing water quality to determine if it's safe for human consumption, using various metrics like pH, hardness, and more, from the "water_potability.csv" dataset. The goal is to predict water potability, where '1' means the water is safe to drink, and '0' means it's not.

## Project Structure

```
Error418/
│
├── data/
│   ├── water_potability_expanded.csv
│   ├── water_potability_with_errors.csv
│   └── water_potability.csv
│
├── docker/
│   └── airflow/
│       ├── config/
│       ├── dags/
│       │   ├── raw_data/
│       │   │   └── ... (csv files)
│       │   ├── bad_data/
│       │   │   └── ... (csv files)
│       │   ├── good_data/
│       │   │   └── ... (csv files)
│       │   ├── data-ingestion-dag.py
│       │   └── first_dag.py
│       ├── gx/
│       │   ├── checkpoints/
│       │   ├── expectations/
│       │   ├── plugins/
│       │   ├── profilers/
│       │   ├── uncommitted/
│       │   ├── .gitignore
│       │   └── great_expectations.yml
│       ├── logs/
│       ├── plugins/
│       ├── docker-compose.yaml
│       ├── Dockerfile
│       └── requirements.txt
│
```

## Prerequisites

Make sure you have the following installed:
- Python 3.8 or higher
- pip (Python package installer)
- Docker (for running Airflow)
- PostgreSQL (or any SQL-compatible database)

## Setup Instructions

### Step 1: Clone the Repository

Clone this repository to your local machine using:

```bash
git clone <repository_url>
cd Error418
```

### Step 2: Setup the Environment

#### Install Python Dependencies

Navigate to the project directory and install the necessary Python packages:

```bash
pip install -r requirements.txt
```

#### Setup Great Expectations

Initialize Great Expectations in your project:

```bash
great_expectations init
```

This will create a `great_expectations` directory in your project. Configure it as needed.

### Step 3: Run the API

Navigate to the API directory and run the FastAPI application using Uvicorn:

```bash
cd API
uvicorn app:app --reload
```

This will start the FastAPI server on [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Step 4: Run the Streamlit Application

Navigate to the Streamlit directory and start the Streamlit application:

```bash
cd ../streamlit
streamlit run streamlit.py
```

This will start the Streamlit app on [http://localhost:8501](http://localhost:8501).

### Step 5: Set Up Airflow for Data Ingestion and Validation

#### Airflow Setup Using Docker

Pull the Airflow Docker image:

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.9.1/docker-compose.yaml'
```

Create an `.env` file for Airflow:

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

Start Airflow services:

```bash
docker-compose up airflow-init
docker-compose up
```

This will start the Airflow webserver, scheduler, and other necessary services.

Access the Airflow UI:
Open your browser and go to [http://localhost:8080](http://localhost:8080). Use the default credentials (`airflow`/`airflow`) to log in.

### Step 6: Validate Data with Great Expectations

Make sure the Great Expectations directory (`gx`) is properly configured. You can run the validation suite manually or through the Airflow DAG:

```bash
great_expectations suite edit <expectation_suite_name>
```

## Project Components

### API

The API component uses FastAPI to serve a machine learning model that predicts water potability based on the input features. It also logs predictions to a PostgreSQL database.

### Streamlit

The Streamlit component provides a user-friendly interface for users to input water quality metrics and get real-time predictions. It also allows users to upload CSV files for batch predictions.

### Airflow DAG

The Airflow DAG is designed to automate the process of ingesting, validating, and processing data. It includes tasks to:
- Read data from the `raw_data` folder.
- Validate data using Great Expectations.
- Split data into `good_data` and `bad_data` based on validation results.
- Log data quality statistics to the database.
- Send alerts for data quality issues.
