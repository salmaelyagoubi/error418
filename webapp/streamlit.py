import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime 

# Set page configuration
st.set_page_config(
    page_title='Water Prediction',
    page_icon='💧',
    layout='wide',
    initial_sidebar_state='auto'
)

# Function to make predictions using the API
def make_prediction(api_url, input_data, source):
    try:
        payload = {
            "input_data": input_data,
            "source": source
        }
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to get prediction from the server. Status Code: " + str(response.status_code))
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the server. Please make sure the API server is running.")
    return None


# Function to retrieve past predictions using the API
def get_past_predictions(api_url, payload):
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to get past predictions from the server. Status Code: " + str(response.status_code))
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the server. Please make sure the API server is running.")
    return None

def prediction_page():
    st.title("Make Water Quality Predictions")

    # Single Sample Prediction Form
    st.write("### Single Sample Prediction")
    with st.form(key='single_sample_form'):
        features = [
            'ph', 
            'Hardness', 
            'Solids', 
            'Chloramines', 
            'Sulfate', 
            'Conductivity', 
            'Organic_carbon', 
            'Trihalomethanes', 
            'Turbidity'
        ]
        input_data = {feature: st.number_input(f'Enter {feature}', step=1.0, format="%.2f") for feature in features}
        submit_single = st.form_submit_button("Predict Single Sample")

    if submit_single:
        single_prediction = make_prediction("http://127.0.0.1:8000/predict", [input_data], "webapp")
        if single_prediction:
            st.success("Single prediction received from the backend.")
            result_df = pd.DataFrame([input_data], index=['Input Data'])
            result_df['Prediction'] = single_prediction['prediction'][0]
            st.dataframe(result_df)

    # Multiple Sample Prediction from CSV
    st.write("### Multiple Sample Prediction")
    uploaded_file = st.file_uploader("Upload CSV for prediction", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        data.fillna(0, inplace=True)  # Clean the data
        data.replace([np.inf, -np.inf], 0, inplace=True)
        if st.button("Predict Multiple Samples"):
            multiple_predictions = make_prediction("http://127.0.0.1:8000/predict", data.to_dict(orient='records'), "scheduled")
            if multiple_predictions:
                st.success("Multiple predictions received from the backend.")
                results_df = pd.DataFrame(multiple_predictions['prediction'], columns=['Result'])
                display_df = pd.concat([data.reset_index(drop=True), results_df], axis=1)
                st.dataframe(display_df)

# Past Predictions Page
def past_predictions_page():
    st.title("View Past Water Quality Predictions")

    # Date Range and Source Selector
    with st.form(key='date_source_form'):
        start_date = st.date_input("Start Date", datetime.now())
        end_date = st.date_input("End Date", datetime.now())
        prediction_source = st.selectbox("Select Source of Predictions", ['webapp', 'scheduled', 'all'])
        submit_past = st.form_submit_button("Retrieve Predictions")

    if submit_past:
        payload = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "source": prediction_source
        }
        past_predictions = get_past_predictions("http://127.0.0.1:8000/get-past-predictions", payload)
        if past_predictions:
            st.success("Past predictions received from the backend.")
            past_predictions_df = pd.DataFrame(past_predictions)
            st.dataframe(past_predictions_df)



st.sidebar.title("Navigation 💧")
choice = st.sidebar.radio("Choose a Page:", ["Prediction Page", "Past Predictions Page"])

if choice == "Prediction Page":
    prediction_page()
elif choice == "Past Predictions Page":
    past_predictions_page()
