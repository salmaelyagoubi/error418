import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from joblib import dump
from .constant import DATA_FILE_PATH, RANDOM_STATE, TEST_SIZE

def preprocess_data():
    data = pd.read_csv(DATA_FILE_PATH)
    X = data.drop('Potability', axis=1)
    y = data['Potability']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

    imputer = SimpleImputer(strategy='mean')
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    dump(imputer, '../model/imputer.joblib')

    return X_train_imputed, X_test_imputed, y_train, y_test, imputer