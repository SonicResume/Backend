from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "ok",
        "service": "face-api",
        "message": "server running"
    }
