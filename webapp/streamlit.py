from io import StringIO
import json
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title='Water prediction',
    page_icon='',
    layout='wide',
    initial_sidebar_state='auto'
)

def main():
    st.title("Water prediction ")
    prediction_page()

def prediction_page():
    st.write("Water Quality Prediction Page")

    with st.form(key='prediction_form'):
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

        input_data = {}
        for feature in features:
            input_data[feature] = st.number_input(f'Enter {feature}', step=1.0, format="%.2f")
        get_prediction = st.form_submit_button(label='Check Water Quality')

    if get_prediction:
        url = 'http://127.0.0.1:8000/predict'
        try:
            response = requests.post(url, json=input_data)
            if response.status_code == 200:
                prediction = response.json()
                st.success("Prediction received from the backend.")
                st.write(f"Prediction: {prediction['prediction']}")
                received_data = prediction['received_data']
                received_data_df = pd.DataFrame([received_data])
                st.subheader("Received Data")
                st.dataframe(received_data_df)
            else:
                st.error("Failed to get prediction from the server.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the server. Please make sure the API server is running.")

    st.write("Past Water Quality Predictions")
    get_past_predictions = st.button('Get Past Predictions')

    if get_past_predictions:
            past_predictions_url = 'http://127.0.0.1:8000/get-past-predictions'
            try:
                past_predictions_response = requests.post(past_predictions_url)
                if past_predictions_response.status_code == 200:
                    past_predictions = past_predictions_response.json()
                    st.success("Past predictions received from the backend.")
                    past_predictions_df = pd.DataFrame(past_predictions)
                    st.dataframe(past_predictions_df)
                else:
                    st.error("Failed to get past predictions from the server.")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the server. Please make sure the API server is running.")

if __name__ == "__main__":
    main()