from fastapi import FastAPI

app = FastAPI(
    title="Mapa Psíquico API",
    version="0.1.0",
    description="Motor de cálculo arquetípico — converte nome + data/hora/local em IDs (1–33).",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
