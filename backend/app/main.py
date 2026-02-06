from fastapi import FastAPI

app = FastAPI(title="Stock Exchange Prediction API")

@app.get("/home")
def welcome_message():
    return {"message": "Welcome to the Stock Exchange Prediction API"}
