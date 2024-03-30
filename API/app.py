from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
import pandas as pd
from joblib import load
import json
import psycopg2
from dotenv import load_dotenv
import os  

# Load your model and imputer
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
cursor = conn.cursor()  # Ensure cursor is defined here after connection

# Create the predictions table if it does not exist
create_table_query = """
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    input_features JSONB,
    prediction INTEGER
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
def predict(input_data: PredictionInput):
    input_df = pd.DataFrame([input_data.dict()])
    input_imputed = imputer.transform(input_df)
    prediction = model.predict(input_imputed)
    prediction_list = prediction.tolist()

    input_features_json = json.dumps(input_data.dict())
    insert_query = "INSERT INTO predictions (input_features, prediction) VALUES (%s, %s)"
    cursor.execute(insert_query, (input_features_json, prediction_list[0]))
    conn.commit()

    return {"received_data": input_data.dict(), "prediction": "Bad quality" if prediction_list[0] == 0 else "Good quality"}

@app.post('/get-past-predictions')
def predict():
    select_query = "SELECT * FROM predictions"
    cursor.execute(select_query)
    past_predictions = cursor.fetchall()
    past_predictions_list = []
    for prediction in past_predictions:
        past_predictions_list.append({
            "input_features": prediction[1],
            "prediction": "Bad quality" if prediction[2] == 0 else "Good quality"
        })
    return past_predictions_list
    