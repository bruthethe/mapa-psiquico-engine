from fastapi import FastAPI

app = FastAPI(
    title="Esoteric Calculation Engine API",
    version="0.1.0",
    description="Astronomical and esoteric calculation engine.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
