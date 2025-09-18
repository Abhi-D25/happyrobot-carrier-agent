from fastapi import APIRouter, Depends
from api.deps import require_api_key
from api.schemas import NegotiationRequest, NegotiationResponse
from api.services.negotiation_policy import NegotiationPolicy
from pydantic import BaseModel

class NegotiationEvaluateRequest(BaseModel):
    listed_rate: float
    offer: float
    round: int = 1
    market_average: float = None
    broker_minimum: float = None

router = APIRouter()

@router.post("/negotiation/evaluate", response_model=NegotiationResponse)
async def evaluate_negotiation(
    request: NegotiationEvaluateRequest,
    api_key: str = Depends(require_api_key)
):
    """
    Evaluate negotiation using the recommended 3-round market-based formula.
    
    3-ROUND NEGOTIATION FORMULA:
    - Initial Offer: Start 15% below market average
    - First Counter: Move 30% of difference between initial offer and carrier's ask
    - Final Counter: Approach fair market rate, leaving small margin for profit
    
    Parameters:
    - listed_rate: The original listed rate for the load
    - offer: The carrier's current offer
    - round: Current negotiation round (1-3)
    - market_average: Market average rate for this lane (optional, defaults to listed_rate)
    - broker_minimum: Broker's minimum/walk-away price (optional, defaults to 85% of listed_rate)
    """
    try:
        policy = NegotiationPolicy()
        result = policy.evaluate_offer(
            listed_rate=request.listed_rate,
            offer=request.offer,
            round_number=request.round,
            market_average=request.market_average,
            broker_minimum=request.broker_minimum
        )
        
        return NegotiationResponse(
            ok=True,
            data=result
        )
        
    except Exception as e:
        return NegotiationResponse(
            ok=False,
            error=f"Negotiation evaluation failed: {str(e)}"
        )

@router.get("/negotiation/summary")
async def get_negotiation_summary(
    listed_rate: float,
    api_key: str = Depends(require_api_key)
):
    """
    Get negotiation parameters summary for a given listed rate.
    """
    try:
        policy = NegotiationPolicy()
        summary = policy.get_negotiation_summary(listed_rate)
        
        return {
            "ok": True,
            "data": summary
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to get negotiation summary: {str(e)}"
        }
