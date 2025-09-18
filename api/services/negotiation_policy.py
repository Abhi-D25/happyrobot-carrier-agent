"""
Enhanced negotiation policy service with carrier-aware counter-offers.
"""
from typing import Dict, Any
from enum import Enum

class NegotiationOutcome(Enum):
    ACCEPT = "accept"
    COUNTER = "counter"
    REJECT = "reject"
    MAX_ROUNDS_REACHED = "max_rounds_reached"

class NegotiationPolicy:
    """Policy engine for load negotiations with market-based 3-round formula."""
    
    def __init__(self):
        self.max_rounds = 3  # Maximum 3 rounds of negotiation
        
        # Market-based parameters (can be configured per lane/load)
        self.market_average_multiplier = 0.85  # Start 15% below market average
        self.broker_minimum_multiplier = 0.85  # Broker's minimum (walk-away price)
        self.fair_market_multiplier = 1.0  # Fair market rate
        
        # Negotiation strategy parameters
        self.first_counter_move_percentage = 0.30  # Move 30% of difference in first counter
        self.final_counter_move_percentage = 0.80  # Move 80% toward fair market in final round
    
    def evaluate_offer(self, listed_rate: float, offer: float, round_number: int, 
                      market_average: float = None, broker_minimum: float = None) -> Dict[str, Any]:
        """
        Evaluate a carrier's offer using the recommended 3-round negotiation formula.
        
        Formula:
        - Initial Offer: Start at or slightly below market average (10-15% below)
        - First Counter: Move 25-40% of difference between initial offer and carrier's ask
        - Final Counter: Approach fair market rate, leaving small margin for profit
        
        Args:
            listed_rate: The original listed rate for the load
            offer: The carrier's current offer
            round_number: Current negotiation round (1-based)
            market_average: Market average rate for this lane (defaults to listed_rate)
            broker_minimum: Broker's minimum/walk-away price (defaults to 85% of listed_rate)
            
        Returns:
            Dictionary with evaluation result
        """
        # Set defaults if market data not provided
        if market_average is None:
            market_average = listed_rate
        if broker_minimum is None:
            broker_minimum = listed_rate * self.broker_minimum_multiplier
        
        # Calculate key rates
        initial_offer = market_average * self.market_average_multiplier  # 15% below market
        fair_market_rate = listed_rate * self.fair_market_multiplier
        
        # Reject if offer is below broker minimum (walk-away price)
        if offer < broker_minimum:
            return {
                "outcome": NegotiationOutcome.REJECT.value,
                "message": f"Cannot accept below our minimum rate of ${broker_minimum:.2f}",
                "market_average": market_average,
                "initial_offer": initial_offer,
                "fair_market_rate": fair_market_rate,
                "broker_minimum": broker_minimum,
                "counter_offer": None,
                "round": round_number,
                "max_rounds": self.max_rounds
            }
        
        # Accept immediately if offer is at or below our initial offer
        if offer <= initial_offer:
            return {
                "outcome": NegotiationOutcome.ACCEPT.value,
                "message": f"Offer accepted at ${offer:.2f} - excellent rate!",
                "market_average": market_average,
                "initial_offer": initial_offer,
                "fair_market_rate": fair_market_rate,
                "broker_minimum": broker_minimum,
                "counter_offer": None,
                "round": round_number,
                "max_rounds": self.max_rounds,
                "accepted_rate": offer
            }
        
        # Check if we've reached max rounds
        if round_number >= self.max_rounds:
            # Final round: accept if reasonable, otherwise walk away
            if offer <= fair_market_rate:
                return {
                    "outcome": NegotiationOutcome.ACCEPT.value,
                    "message": f"Final round - accepting offer at ${offer:.2f}",
                    "market_average": market_average,
                    "initial_offer": initial_offer,
                    "fair_market_rate": fair_market_rate,
                    "broker_minimum": broker_minimum,
                    "counter_offer": None,
                    "round": round_number,
                    "max_rounds": self.max_rounds,
                    "accepted_rate": offer
                }
            else:
                return {
                    "outcome": NegotiationOutcome.REJECT.value,
                    "message": "Maximum rounds reached - cannot reach agreement",
                    "market_average": market_average,
                    "initial_offer": initial_offer,
                    "fair_market_rate": fair_market_rate,
                    "broker_minimum": broker_minimum,
                    "counter_offer": None,
                    "round": round_number,
                    "max_rounds": self.max_rounds
                }
        
        # Calculate counter-offer using the 3-round formula
        counter_offer = self._calculate_3_round_counter(
            initial_offer, offer, round_number, fair_market_rate, broker_minimum
        )
        
        return {
            "outcome": NegotiationOutcome.COUNTER.value,
            "message": f"Counter offer: ${counter_offer:.2f}",
            "market_average": market_average,
            "initial_offer": initial_offer,
            "fair_market_rate": fair_market_rate,
            "broker_minimum": broker_minimum,
            "counter_offer": counter_offer,
            "round": round_number,
            "max_rounds": self.max_rounds
        }
    
    def _calculate_3_round_counter(self, initial_offer: float, carrier_offer: float, 
                                  round_number: int, fair_market_rate: float, 
                                  broker_minimum: float) -> float:
        """
        Calculate counter-offer using the recommended 3-round negotiation formula.
        
        Formula:
        - Round 1: Move 25-40% of difference between initial offer and carrier's ask
        - Round 2: Move closer to fair market rate
        - Round 3: Approach fair market rate, leaving small margin for profit
        
        Args:
            initial_offer: Our initial offer (15% below market average)
            carrier_offer: Carrier's current offer
            round_number: Current round (1-based)
            fair_market_rate: Fair market rate for this lane
            broker_minimum: Broker's minimum/walk-away price
            
        Returns:
            Counter offer amount rounded to nearest $10
        """
        if round_number == 1:
            # First Counter: Move 25-40% of difference between initial offer and carrier's ask
            difference = carrier_offer - initial_offer
            move_amount = difference * self.first_counter_move_percentage  # 30% of difference
            counter = initial_offer + move_amount
            
        elif round_number == 2:
            # Second Counter: Move closer to fair market rate
            # Move 60% of remaining difference toward fair market
            remaining_difference = fair_market_rate - initial_offer
            move_amount = remaining_difference * 0.60
            counter = initial_offer + move_amount
            
        else:  # Round 3
            # Final Counter: Approach fair market rate, leaving small margin
            # Move 80% toward fair market rate
            remaining_difference = fair_market_rate - initial_offer
            move_amount = remaining_difference * self.final_counter_move_percentage  # 80%
            counter = initial_offer + move_amount
        
        # Ensure counter is within reasonable bounds
        counter = max(counter, broker_minimum)  # Never below broker minimum
        counter = min(counter, fair_market_rate)  # Never above fair market
        
        return self._round_to_nearest_10(counter)
    
    def _round_to_nearest_10(self, amount: float) -> float:
        """Round amount to nearest $10."""
        return round(amount / 10) * 10
    
    def get_negotiation_summary(self, listed_rate: float, market_average: float = None) -> Dict[str, Any]:
        """
        Get a summary of the negotiation parameters for a load using the 3-round formula.
        
        Args:
            listed_rate: The original listed rate for the load
            market_average: Market average rate for this lane (defaults to listed_rate)
            
        Returns:
            Dictionary with negotiation parameters
        """
        if market_average is None:
            market_average = listed_rate
            
        initial_offer = market_average * self.market_average_multiplier
        fair_market_rate = listed_rate * self.fair_market_multiplier
        broker_minimum = listed_rate * self.broker_minimum_multiplier
        
        return {
            "listed_rate": listed_rate,
            "market_average": market_average,
            "initial_offer": initial_offer,
            "fair_market_rate": fair_market_rate,
            "broker_minimum": broker_minimum,
            "max_rounds": self.max_rounds,
            "policy": {
                "market_average_multiplier": self.market_average_multiplier,
                "broker_minimum_multiplier": self.broker_minimum_multiplier,
                "fair_market_multiplier": self.fair_market_multiplier,
                "first_counter_move_percentage": self.first_counter_move_percentage,
                "final_counter_move_percentage": self.final_counter_move_percentage,
                "strategy": "3-Round Market-Based Negotiation Formula",
                "description": "Start 15% below market, move 30% of difference in round 1, approach fair market in final round"
            }
        }