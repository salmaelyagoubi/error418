from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List
import pandas as pd
from joblib import load
import json
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional
import os
from datetime import datetime , timedelta
# Load models and environment variables
model = load('../model/model.joblib')
imputer = load('../model/imputer.joblib')

load_dotenv()  # Load environment variables from .env file

# Database connection
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
cursor = conn.cursor()

# Ensure predictions table exists with timestamp column
create_table_query = """
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    input_features JSONB,
    prediction INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(255)
);
"""
cursor.execute(create_table_query)
conn.commit()

app = FastAPI()

class PredictionInput(BaseModel):
    ph: float
    Hardness: float
    Solids: float
    Chloramines: float
    Sulfate: float
    Conductivity: float
    Organic_carbon: float
    Trihalomethanes: float
    Turbidity: float

@app.post('/predict')
def predict(input_data: List[PredictionInput]):
    input_df = pd.DataFrame([item.dict() for item in input_data])
    input_imputed = imputer.transform(input_df)
    prediction = model.predict(input_imputed)
    prediction_list = prediction.tolist()

    # Insert predictions along with the timestamp
    for idx, input_item in enumerate(input_data):
        input_features_json = json.dumps(input_item.dict())
        insert_query = "INSERT INTO predictions (input_features, prediction) VALUES (%s, %s)"
        cursor.execute(insert_query, (input_features_json, prediction_list[idx]))
    conn.commit()

    return {"received_data": [item.dict() for item in input_data], "prediction": ["Bad quality" if pred == 0 else "Good quality" for pred in prediction_list]}

class PastPredictionsQuery(BaseModel):
    start_date: Optional[str]
    end_date: Optional[str]
    source: Optional[str] = "all"

@app.post('/get-past-predictions')
def get_past_predictions(query: PastPredictionsQuery = Body(...)):
    try:
        # Parse the start and end dates
        if query.start_date:
            start_date = datetime.strptime(query.start_date, "%Y-%m-%d")
        else:
            start_date = None

        if query.end_date:
            end_date = datetime.strptime(query.end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        else:
            end_date = None

        if start_date and end_date and start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date.")

        # Build the query with date filters
        select_query = "SELECT * FROM predictions WHERE 1=1"
        query_params = []

        if start_date:
            select_query += " AND timestamp >= %s"
            query_params.append(start_date)
        if end_date:
            select_query += " AND timestamp <= %s"
            query_params.append(end_date)

        if query.source and query.source != "all":
            select_query += " AND input_features->>'source' = %s"
            query_params.append(query.source)

        cursor.execute(select_query, query_params)
        past_predictions = cursor.fetchall()

        past_predictions_list = []
        for prediction in past_predictions:
            timestamp = prediction[3].isoformat() if prediction[3] else None
            past_predictions_list.append({
                "input_features": prediction[1],
                "prediction": "Bad quality" if prediction[2] == 0 else "Good quality",
                "timestamp": timestamp 
            })

        return past_predictions_list

    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from e