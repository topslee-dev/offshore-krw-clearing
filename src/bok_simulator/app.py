import uvicorn

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    FastAPI = None
    BaseModel = None
    HTTPException = None

from src.bok_simulator.handlers import BOKMessageHandler
from src.bok_simulator.scenarios import ScenarioEngine

if FastAPI is not None:

    class MessageRequest(BaseModel):
        raw_message: str

    class RejectRequest(BaseModel):
        reason: str
        original_message: str = ""

    app = FastAPI(title="BOK SWIFT Gateway Simulator", version="1.0.0")
    handler = BOKMessageHandler()
    scenario_engine = ScenarioEngine()

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }

    @app.post("/swift/inbound/mt103")
    async def receive_mt103(request: MessageRequest):
        result = handler.handle_mt103(request.raw_message)
        return result

    @app.post("/swift/inbound/mt202")
    async def receive_mt202(request: MessageRequest):
        result = handler.handle_mt202(request.raw_message)
        return result

    @app.post("/swift/simulate/reject")
    async def simulate_rejection(request: RejectRequest):
        result = scenario_engine.test_scenario(
            request.reason, request.original_message
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result

    def run(host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(app, host=host, port=port)

else:
    app = None
    handler = BOKMessageHandler()
    scenario_engine = ScenarioEngine()

    def run(host: str = "0.0.0.0", port: int = 8000):
        print("FastAPI is not installed. Install with: pip install fastapi uvicorn")
