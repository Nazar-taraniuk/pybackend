from fastapi import FastAPI

app = FastAPI(
    title="PyBackend",
    description="FastAPI college project",
    version="0.1.0",
)


@app.get("/", tags=["root"])
async def root():
    """Health check endpoint."""
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    """Health status."""
    return {"status": "ok"}
