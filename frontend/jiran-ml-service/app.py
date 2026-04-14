from fastapi import FastAPI
import joblib
import pandas as pd
import numpy as np

app = FastAPI()

# Load models at startup
model = joblib.load("saved_models/stock_classifier.pkl")
scaler = joblib.load("saved_models/scaler.pkl")
category_encoder = joblib.load("saved_models/label_encoder.pkl")


@app.get("/")
def root():
    return {"message": "Jiran ML Service running"}


@app.post("/predict-stock")
def predict_stock(data: dict):

    df = pd.DataFrame(data["products"])

    # Encode category
    df["category_encoded"] = category_encoder.transform(
        df["category"].fillna("unknown")
    )

    # Select model features
    features = df[[
        "stock_quantity",
        "sales_last_7d",
        "sales_last_30d",
        "category_encoded"
    ]]

    # Scale
    features_scaled = scaler.transform(features)

    # Predict
    preds = model.predict(features_scaled)
    probs = model.predict_proba(features_scaled).max(axis=1)

    df["prediction"] = preds
    df["confidence"] = probs

    return {
        "insights": df[[
            "product_name",
            "prediction",
            "confidence"
        ]].to_dict(orient="records")
    }