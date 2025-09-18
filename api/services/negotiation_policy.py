from typing import Dict, Any
from enum import Enum

class NegotiationOutcome(Enum):
    ACCEPT = "accept"
    COUNTER = "counter"
    REJECT = "reject"
    MAX_ROUNDS_REACHED = "max_rounds_reached"

class NegotiationPolicy:
    """Policy engine for load negotiations with proper broker-carrier dynamics."""
    
    def __init__(self):
        self.max_rounds = 3  # Maximum 3 rounds of negotiation
        
        # Broker perspective: We want to pay LESS, carriers want MORE
        self.initial_offer_multiplier = 0.85  # Start 15% below market average
        self.acceptance_threshold = 1.05      # Accept if carrier asks <= 5% above listed
        self.walk_away_threshold = 1.20       # Walk away if carrier asks >20% above listed
        
    def evaluate_offer(self, listed_rate: float, carrier_ask: float, round_number: int, 
                      market_average: float = None, broker_maximum: float = None) -> Dict[str, Any]:
        """
        Evaluate a carrier's rate REQUEST (they want MORE money).
        
        Corrected Logic:
        - Carrier asks: "I want $2,200 for this load"
        - Listed rate: $2,000 (what we posted)
        - We evaluate: Can we accept $2,200? Should we counter with less?
        
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
        
        # REJECT if carrier asks too much (above our walk-away price)
        if carrier_ask > broker_maximum:
            return {
                "outcome": NegotiationOutcome.REJECT.value,
                "message": f"I understand you need ${carrier_ask:.2f}, but our maximum budget for this load is ${broker_maximum:.2f}. We can't go higher than that.",
                "listed_rate": listed_rate,
                "market_average": market_average,
                "broker_maximum": broker_maximum,
                "acceptance_threshold": acceptance_threshold,
                "counter_offer": None,
                "round": round_number,
                "max_rounds": self.max_rounds
            }
        
        # Check if we've reached max rounds
        if round_number >= self.max_rounds:
            # Final round: accept if within our maximum, otherwise walk away
            if carrier_ask <= broker_maximum:
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
                return {
                    "outcome": NegotiationOutcome.REJECT.value,
                    "message": "We've reached our final round and can't meet your rate request. Thank you for your time.",
                    "listed_rate": listed_rate,
                    "market_average": market_average,
                    "broker_maximum": broker_maximum,
                    "acceptance_threshold": acceptance_threshold,
                    "counter_offer": None,
                    "round": round_number,
                    "max_rounds": self.max_rounds
                }
        
        # Calculate counter-offer (we offer LESS than what they're asking)
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
            "message": f"I understand you're looking for ${carrier_ask:.2f}. How about we meet at ${counter_offer:.2f}?",
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
        
        Broker Logic: We start low and gradually move UP toward the carrier's ask,
        but never exceed our maximum budget.
        
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
            # First Counter: Move 25-40% of difference between our initial offer and their ask
            difference = carrier_ask - initial_offer
            move_percentage = 0.30  # Move 30% toward their ask
            counter = initial_offer + (difference * move_percentage)
            
        elif round_number == 2:
            # Second Counter: Move closer to fair market (our listed rate)
            # This is typically around the middle ground
            counter = (initial_offer + listed_rate) / 2
            
        else:  # Round 3+
            # Final Counter: Move toward our maximum, but stay below carrier ask
            # Move 75% toward our maximum from initial offer
            difference = broker_maximum - initial_offer
            counter = initial_offer + (difference * 0.75)
        
        # Ensure counter is within reasonable bounds
        counter = max(counter, initial_offer)      # Never below our initial offer
        counter = min(counter, broker_maximum)     # Never above our maximum
        counter = min(counter, carrier_ask * 0.98) # Always slightly below their ask
        
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
                "strategy": "3-Round Broker Negotiation (Carriers ask for MORE, we counter with LESS)",
                "description": "Accept reasonable asks (≤5% above listed), counter progressively higher, walk away if >20% above listed"
            }
        }