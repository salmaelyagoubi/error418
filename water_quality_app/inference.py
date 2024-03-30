
import pandas as pd
from joblib import load
from .constant import DATA_FILE_PATH

def predict(model, imputer):
    new_data = pd.read_csv(DATA_FILE_PATH)
    new_data_features = new_data.drop('Potability', axis=1)
    new_data_imputed = imputer.transform(new_data_features)

    new_predictions = model.predict(new_data_imputed)

    return new_predictions