from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle

app = FastAPI()

# --- Load models ---
with open("category_encoder.pkl", "rb") as f:
    category_encoder = pickle.load(f)

with open("stock_model.pkl", "rb") as f:
    stock_model = pickle.load(f)

# --- Pydantic model for request ---
class Product(BaseModel):
    product_name: str
    category: str
    stock_quantity: int
    sales_last_7d: int
    sales_last_30d: int

class StockRequest(BaseModel):
    products: list[Product]

# --- Safe transform function ---
def safe_transform(encoder, values):
    """Encode categories; unseen categories become -1"""
    encoded = []
    for v in values:
        if v in encoder.classes_:
            encoded.append(int(encoder.transform([v])[0]))
        else:
            encoded.append(-1)  # default for unknown category
    return encoded

# --- Prediction endpoint ---
@app.post("/predict-stock")
def predict_stock(data: StockRequest):
    try:
        # Convert request to DataFrame
        df = pd.DataFrame([p.dict() for p in data.products])

        # Encode categories safely
        df["category_encoded"] = safe_transform(category_encoder, df["category"])

        # Features for the model
        features = df[["stock_quantity", "sales_last_7d", "sales_last_30d", "category_encoded"]]

        # Make predictions
        predictions = stock_model.predict(features)
        confidences = stock_model.predict_proba(features).max(axis=1)

        # Return results
        results = []
        for pred, conf in zip(predictions, confidences):
            results.append({"prediction": pred, "confidence": float(conf)})

        return {"results": results}

    except Exception as e:
        # Catch any error and return friendly message
        raise HTTPException(status_code=500, detail=str(e))