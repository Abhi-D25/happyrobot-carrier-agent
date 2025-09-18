from typing import Dict, Any
from enum import Enum

class NegotiationOutcome(Enum):
    ACCEPT = "accept"
    COUNTER = "counter"
    REJECT = "reject"
    MAX_ROUNDS_REACHED = "max_rounds_reached"

class NegotiationPolicy:
    """Fixed policy engine for load negotiations with proper 3-round handling."""
    
    def __init__(self):
        self.max_rounds = 3
        self.acceptance_threshold = 1.05      # Accept up to 5% above listed
        self.walk_away_threshold = 1.20       # Walk away only after 3 rounds
        self.initial_offer_multiplier = 0.85  # Our initial counters start 15% below market
        
    def evaluate_offer(self, listed_rate: float, carrier_ask: float, round_number: int, 
                      market_average: float = None, broker_maximum: float = None) -> Dict[str, Any]:
        """
        Evaluate a carrier's rate REQUEST with proper 3-round negotiation.
        
        FREIGHT BROKER LOGIC:
        - Start negotiations from the quoted/listed rate (what agent told carrier)
        - Always negotiate for rounds 1 and 2, regardless of how high the ask is
        - Only reject in round 3 if still above our maximum budget
        - Move upward from our quoted rate when carrier asks for more
        
        Args:
            listed_rate: The rate we quoted to the carrier (our starting point)
            carrier_ask: The rate the carrier is REQUESTING (usually higher)
            round_number: Current negotiation round (1-based)
            market_average: Market average rate (defaults to listed_rate)
            broker_maximum: Our maximum budget/walk-away price
            
        Returns:
            Dictionary with evaluation result
        """
        # Set defaults if market data not provided
        if market_average is None:
            market_average = listed_rate
        if broker_maximum is None:
            broker_maximum = listed_rate * self.walk_away_threshold  # 20% above listed
        
        # Calculate key rates - use listed_rate as our baseline (what we quoted)
        quoted_rate = listed_rate  # This is what the agent told the carrier
        acceptance_threshold = listed_rate * self.acceptance_threshold  # Accept up to 5% above listed
        
        # ACCEPT if carrier's ask is reasonable (at or below our acceptance threshold)
        if carrier_ask <= acceptance_threshold:
            return {
                "outcome": NegotiationOutcome.ACCEPT.value,
                "message": f"Great! We can work with ${carrier_ask:.2f}. Let's get the paperwork started.",
                "listed_rate": listed_rate,
                "market_average": market_average,
                "broker_maximum": broker_maximum,
                "acceptance_threshold": acceptance_threshold,
                "counter_offer": None,
                "round": round_number,
                "max_rounds": self.max_rounds,
                "accepted_rate": carrier_ask
            }
        
        # FIXED: Only reject if we've reached max rounds AND they're still above our maximum
        if round_number >= self.max_rounds:
            if carrier_ask <= broker_maximum:
                # Final round: accept if within our maximum
                return {
                    "outcome": NegotiationOutcome.ACCEPT.value,
                    "message": f"This is our final round. We can accept ${carrier_ask:.2f}.",
                    "listed_rate": listed_rate,
                    "market_average": market_average,
                    "broker_maximum": broker_maximum,
                    "acceptance_threshold": acceptance_threshold,
                    "counter_offer": None,
                    "round": round_number,
                    "max_rounds": self.max_rounds,
                    "accepted_rate": carrier_ask
                }
            else:
                # Final round: reject if still above maximum
                return {
                    "outcome": NegotiationOutcome.REJECT.value,
                    "message": f"I understand you need ${carrier_ask:.2f}, but our maximum budget for this load is ${broker_maximum:.2f}. Thank you for your time.",
                    "listed_rate": listed_rate,
                    "market_average": market_average,
                    "broker_maximum": broker_maximum,
                    "acceptance_threshold": acceptance_threshold,
                    "counter_offer": None,
                    "round": round_number,
                    "max_rounds": self.max_rounds
                }
        
        # FIXED: For rounds 1 and 2, ALWAYS counter regardless of how high their ask is
        counter_offer = self._calculate_broker_counter_from_quoted_rate(
            quoted_rate, carrier_ask, round_number, broker_maximum
        )
        
        # Ensure we never counter with more than what they're asking
        if counter_offer >= carrier_ask:
            # If our counter would be equal or higher, just accept their ask
            return {
                "outcome": NegotiationOutcome.ACCEPT.value,
                "message": f"You know what, ${carrier_ask:.2f} works for us. Let's do it!",
                "listed_rate": listed_rate,
                "market_average": market_average,
                "broker_maximum": broker_maximum,
                "acceptance_threshold": acceptance_threshold,
                "counter_offer": None,
                "round": round_number,
                "max_rounds": self.max_rounds,
                "accepted_rate": carrier_ask
            }
        
        return {
            "outcome": NegotiationOutcome.COUNTER.value,
            "message": f"I understand you're looking for ${carrier_ask:.2f}. Here's what I can do: ${counter_offer:.2f}. How does that work for you?",
            "listed_rate": listed_rate,
            "market_average": market_average,
            "broker_maximum": broker_maximum,
            "acceptance_threshold": acceptance_threshold,
            "counter_offer": counter_offer,
            "round": round_number,
            "max_rounds": self.max_rounds
        }
    
    def _calculate_broker_counter_from_quoted_rate(self, quoted_rate: float, carrier_ask: float, 
                                                  round_number: int, broker_maximum: float) -> float:
        """
        Calculate broker's counter-offer starting from the rate we quoted to the carrier.
        
        FREIGHT BROKER LOGIC: Start from what we quoted and move UP toward their ask.
        
        Args:
            quoted_rate: The rate we told the carrier (our starting point)
            carrier_ask: What the carrier is requesting (usually higher)
            round_number: Current round (1-based)
            broker_maximum: Our walk-away price
            
        Returns:
            Counter offer amount rounded to nearest $10
        """
        # Calculate the gap between our quote and their ask
        gap = carrier_ask - quoted_rate
        
        if round_number == 1:
            # First Counter: Move 25% of the way from our quote toward their ask
            # Conservative first move to leave room for negotiation
            counter = quoted_rate + (gap * 0.25)
            
        elif round_number == 2:
            # Second Counter: Move 50% of the way from our quote toward their ask
            # More generous move to show we're willing to negotiate
            counter = quoted_rate + (gap * 0.50)
            
        else:  # Round 3+
            # Final Counter: Move 75% of the way from our quote toward their ask
            # Our best offer before accept/reject decision
            counter = quoted_rate + (gap * 0.75)
        
        # Ensure counter is within reasonable bounds
        counter = max(counter, quoted_rate)        # Never below what we quoted
        counter = min(counter, broker_maximum)     # Never above our maximum budget
        counter = min(counter, carrier_ask * 0.98) # Stay slightly below their ask
        
        return self._round_to_nearest_10(counter)
    
    def _calculate_broker_counter(self, initial_offer: float, carrier_ask: float, 
                                 round_number: int, broker_maximum: float, 
                                 listed_rate: float) -> float:
        """
        Legacy method - kept for compatibility but not used in new logic.
        """
        # This method is deprecated but kept for any legacy calls
        return self._calculate_broker_counter_from_quoted_rate(listed_rate, carrier_ask, round_number, broker_maximum)
    
    def _round_to_nearest_10(self, amount: float) -> float:
        """Round amount to nearest $10."""
        return round(amount / 10) * 10
    
    def get_negotiation_summary(self, listed_rate: float, market_average: float = None) -> Dict[str, Any]:
        """
        Get a summary of the negotiation parameters.
        
        Args:
            listed_rate: The rate we quoted to the carrier
            market_average: Market average rate (defaults to listed_rate)
            
        Returns:
            Dictionary with negotiation parameters
        """
        if market_average is None:
            market_average = listed_rate
            
        quoted_rate = listed_rate  # What we told the carrier
        acceptance_threshold = listed_rate * self.acceptance_threshold
        broker_maximum = listed_rate * self.walk_away_threshold
        
        return {
            "quoted_rate": quoted_rate,
            "market_average": market_average,
            "acceptance_threshold": acceptance_threshold,
            "broker_maximum": broker_maximum,
            "max_rounds": self.max_rounds,
            "policy": {
                "acceptance_threshold_multiplier": self.acceptance_threshold,
                "walk_away_threshold_multiplier": self.walk_away_threshold,
                "strategy": "3-Round Freight Broker Negotiation (Start from quoted rate)",
                "description": "Quote fair rate upfront, then negotiate upward from quoted rate over 3 rounds",
                "round_progression": {
                    "round_1": "Move 25% from quoted rate toward carrier ask",
                    "round_2": "Move 50% from quoted rate toward carrier ask", 
                    "round_3": "Move 75% from quoted rate toward carrier ask (final offer)"
                }
            }
        }