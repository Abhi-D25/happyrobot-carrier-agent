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
        
        FIXED LOGIC:
        - Always negotiate for rounds 1 and 2, regardless of how high the ask is
        - Only reject in round 3 if still above our maximum budget
        - Carriers ask for MORE money than our listed rate
        
        Args:
            listed_rate: The rate we posted/listed for this load
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
        
        # Calculate key rates
        initial_offer = market_average * self.initial_offer_multiplier  # Our starting offer (15% below market)
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
        counter_offer = self._calculate_broker_counter(
            initial_offer, carrier_ask, round_number, broker_maximum, listed_rate
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
    
    def _calculate_broker_counter(self, initial_offer: float, carrier_ask: float, 
                                 round_number: int, broker_maximum: float, 
                                 listed_rate: float) -> float:
        """
        Calculate broker's counter-offer using the 3-round formula.
        
        FIXED: Now handles high carrier asks properly by gradually moving toward our maximum.
        
        Args:
            initial_offer: Our initial low offer (15% below market)
            carrier_ask: What the carrier is requesting
            round_number: Current round (1-based)
            broker_maximum: Our walk-away price
            listed_rate: Our posted rate
            
        Returns:
            Counter offer amount rounded to nearest $10
        """
        if round_number == 1:
            # First Counter: Move 30% of the way from our initial offer toward our listed rate
            # This gives us room to negotiate upward while staying reasonable
            difference = listed_rate - initial_offer
            counter = initial_offer + (difference * 0.30)
            
        elif round_number == 2:
            # Second Counter: Move to our listed rate (our target rate)
            # This is a fair market rate that we're comfortable with
            counter = listed_rate
            
        else:  # Round 3+
            # Final Counter: Move 75% toward our maximum from our listed rate
            # This is our best and final offer
            difference = broker_maximum - listed_rate
            counter = listed_rate + (difference * 0.75)
        
        # Ensure counter is within reasonable bounds
        counter = max(counter, initial_offer)      # Never below our initial offer
        counter = min(counter, broker_maximum)     # Never above our maximum
        
        # FIXED: Only limit to 98% of their ask if they're asking for a reasonable amount
        # For very high asks, we stick to our calculated counter
        if carrier_ask <= broker_maximum * 1.1:  # If they're asking within 10% of our max
            counter = min(counter, carrier_ask * 0.98)  # Stay slightly below their ask
        
        return self._round_to_nearest_10(counter)
    
    def _round_to_nearest_10(self, amount: float) -> float:
        """Round amount to nearest $10."""
        return round(amount / 10) * 10
    
    def get_negotiation_summary(self, listed_rate: float, market_average: float = None) -> Dict[str, Any]:
        """
        Get a summary of the negotiation parameters.
        
        Args:
            listed_rate: The rate we posted for this load
            market_average: Market average rate (defaults to listed_rate)
            
        Returns:
            Dictionary with negotiation parameters
        """
        if market_average is None:
            market_average = listed_rate
            
        initial_offer = market_average * self.initial_offer_multiplier
        acceptance_threshold = listed_rate * self.acceptance_threshold
        broker_maximum = listed_rate * self.walk_away_threshold
        
        return {
            "listed_rate": listed_rate,
            "market_average": market_average,
            "initial_offer": initial_offer,
            "acceptance_threshold": acceptance_threshold,
            "broker_maximum": broker_maximum,
            "max_rounds": self.max_rounds,
            "policy": {
                "initial_offer_multiplier": self.initial_offer_multiplier,
                "acceptance_threshold_multiplier": self.acceptance_threshold,
                "walk_away_threshold_multiplier": self.walk_away_threshold,
                "strategy": "3-Round Broker Negotiation (Always negotiate for 3 rounds)",
                "description": "Accept reasonable asks (≤5% above listed), always counter for rounds 1-2, final decision in round 3"
            }
        }