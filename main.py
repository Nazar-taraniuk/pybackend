"""
Точка входу в застосунок.
Запускає uvicorn сервер з автоперезавантаженням.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
