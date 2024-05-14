from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
from joblib import load
import json
import psycopg2
from dotenv import load_dotenv
import os

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
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

@app.post('/get-past-predictions')
def get_past_predictions():
    select_query = "SELECT * FROM predictions"
    cursor.execute(select_query)
    past_predictions = cursor.fetchall()
    past_predictions_list = []
    for prediction in past_predictions:
        past_predictions_list.append({
            "input_features": prediction[1],
            "prediction": "Bad quality" if prediction[2] == 0 else "Good quality",
            "timestamp": prediction[3].isoformat()  # Format the timestamp for readability
        })
    return past_predictions_list
