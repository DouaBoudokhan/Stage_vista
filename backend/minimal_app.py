"""Minimal FastAPI app for testing"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Minimal API working"}

@app.get("/test")
def test():
    return {"status": "success", "test": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)