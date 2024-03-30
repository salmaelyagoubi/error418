from sklearn.linear_model import LogisticRegression
from joblib import dump
from .constant import RANDOM_STATE

def build_model(X_train_imputed, y_train):
    model = LogisticRegression(random_state=RANDOM_STATE)
    model.fit(X_train_imputed, y_train)

    dump(model, '../model/model.joblib')

    return model