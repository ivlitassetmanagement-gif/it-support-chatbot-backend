import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # Changed from 8000 to 8001 (avoids port conflicts)
        reload=False
    )
