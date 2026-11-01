from fastapi import FastAPI

from app.api.search import router as search_router

app = FastAPI(title="AI Dev Search")
app.include_router(search_router)


@app.get("/health")
def health():
    return {"status": "ok"}
