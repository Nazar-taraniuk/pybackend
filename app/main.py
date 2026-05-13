from fastapi import FastAPI

from app.routers import users, profiles, categories, products, orders, auth

app = FastAPI(
    title="PyBackend",
    description="FastAPI college project",
    version="0.1.0",
)

# Підключаємо всі роутери
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    return {"status": "ok"}
