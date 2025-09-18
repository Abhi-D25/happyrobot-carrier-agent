import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
from api.services.fmcsa_client import FMCSAClient
from api.services.loads_search import LoadSearchService
from api.services.negotiation_policy import NegotiationPolicy
from api.schemas import LoadSearchRequest

class ConversationState(Enum):
    GREETING = "greeting"
    MC_COLLECTION = "mc_collection"
    MC_VERIFICATION = "mc_verification"
    LOAD_SEARCH = "load_search"
    LOAD_PRESENTATION = "load_presentation"
    NEGOTIATION = "negotiation"
    FINAL_OFFER = "final_offer"
    AGREEMENT = "agreement"
    TRANSFER = "transfer"
    COMPLETE = "complete"
    FAILED = "failed"

class ConversationManager:
    """Manages conversation state and flow for carrier calls."""
    
    def __init__(self, db: Session):
        self.db = db
        self.fmcsa_client = FMCSAClient()
        self.load_service = LoadSearchService(db)
        self.negotiation_policy = NegotiationPolicy()
        self.logger = logging.getLogger(__name__)
        
        # Simple file-based conversation storage for the assessment
        self.conversations_file = Path("conversations.json")
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversations from file."""
        try:
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r') as f:
                    data = json.load(f)
                    # Convert state strings back to enum values
                    for call_id, conversation in data.items():
                        if isinstance(conversation.get("state"), str):
                            try:
                                conversation["state"] = ConversationState(conversation["state"])
                            except ValueError:
                                conversation["state"] = ConversationState.GREETING
                    self.conversations = data
            else:
                self.conversations = {}
        except Exception as e:
            # Log error but continue with empty conversations
            self.logger.error(f"Error loading conversations: {e}")
            self.conversations = {}
    
    def _save_conversations(self):
        """Save conversations to file."""
        try:
            # Convert enum values to strings for JSON serialization
            data_to_save = {}
            for call_id, conversation in self.conversations.items():
                conv_copy = conversation.copy()
                if hasattr(conv_copy.get("state"), 'value'):
                    conv_copy["state"] = conv_copy["state"].value
                data_to_save[call_id] = conv_copy
            
            with open(self.conversations_file, 'w') as f:
                json.dump(data_to_save, f, indent=2, default=str)
        except Exception as e:
            # Log error but continue execution
            self.logger.error(f"Error saving conversations: {e}")
    
    def start_conversation(self, call_id: str) -> Dict[str, Any]:
        """Initialize a new conversation."""
        self.conversations[call_id] = {
            "call_id": call_id,
            "state": ConversationState.GREETING,
            "data": {},
            "negotiation_rounds": 0,
            "created_at": self._get_timestamp()
        }
        self._save_conversations()
        
        return {
            "call_id": call_id,
            "state": ConversationState.GREETING.value,
            "message": "Hello! Thank you for calling. I'm here to help you find loads. May I please get your MC number?",
            "next_action": "collect_mc"
        }
    
    def process_mc_number(self, call_id: str, mc_number: str) -> Dict[str, Any]:
        """Process MC number verification."""
        conversation = self.conversations.get(call_id)
        if not conversation:
            # Auto-initialize if conversation doesn't exist
            self.start_conversation(call_id)
            conversation = self.conversations[call_id]
        
        # Verify with FMCSA
        verification = self.fmcsa_client.verify_carrier(mc_number)
        
        conversation["data"]["mc_number"] = mc_number
        conversation["data"]["fmcsa_verification"] = verification
        
        # Save MC verification status to database
        self._save_mc_verification_to_db(call_id, mc_number, verification)
        
        if verification["eligible"]:
            conversation["state"] = ConversationState.LOAD_SEARCH
            conversation["data"]["carrier_name"] = verification["carrier_name"]
            self._save_conversations()
            
            return {
                "call_id": call_id,
                "state": ConversationState.LOAD_SEARCH.value,
                "verified": True,
                "carrier_name": verification["carrier_name"],
                "message": f"Great! I've verified {verification['carrier_name']}. Where are you looking to pick up loads? I'll need the city and state.",
                "next_action": "collect_origin_location"
            }
        else:
            conversation["state"] = ConversationState.FAILED
            self._save_conversations()
            return {
                "call_id": call_id,
                "state": ConversationState.FAILED.value,
                "verified": False,
                "reason": verification["reason"],
                "message": f"I'm sorry, but I'm unable to work with your carrier at this time. {verification['reason']}",
                "next_action": "end_call"
            }
    
    def search_and_present_loads(self, call_id: str, origin_city: str, origin_state: str,
                           equipment_type: str = None, 
                           destination_city: str = None, destination_state: str = None) -> Dict[str, Any]:
        """Search for loads with detailed city and state matching."""
        conversation = self.conversations.get(call_id)
        if not conversation:
            # Auto-initialize if conversation doesn't exist
            self.start_conversation(call_id)
            conversation = self.conversations[call_id]
        
        # Create enhanced search request
        search_request = LoadSearchRequest(
            equipment_type=equipment_type,
            origin_city=origin_city,
            origin_state=origin_state, 
            destination_city=destination_city,
            destination_state=destination_state,
            limit=5
        )
        
        search_results = self.load_service.search_loads(search_request)
        loads = search_results["loads"]
        
        if not loads:
            # Store search preferences for fallback
            conversation["data"]["search_preferences"] = {
                "equipment_type": equipment_type,
                "origin_city": origin_city,
                "origin_state": origin_state,
                "destination_city": destination_city, 
                "destination_state": destination_state
            }
            
            conversation["state"] = ConversationState.FAILED
            self._save_conversations()
            
            # Provide helpful message about no matching loads
            no_match_message = self._create_no_match_message(
                equipment_type, origin_city, origin_state, 
                destination_city, destination_state
            )
            
            return {
                "call_id": call_id,
                "state": ConversationState.FAILED.value,
                "message": no_match_message,
                "next_action": "offer_alternatives_or_transfer"
            }
        
        # Present the best load
        best_load = loads[0]
        conversation["data"]["presented_load"] = best_load
        conversation["data"]["equipment_type"] = equipment_type
        conversation["data"]["search_preferences"] = {
            "equipment_type": equipment_type,
            "origin_city": origin_city,
            "origin_state": origin_state,
            "destination_city": destination_city,
            "destination_state": destination_state
        }
        conversation["state"] = ConversationState.LOAD_PRESENTATION
        self._save_conversations()
        
        return {
            "call_id": call_id,
            "state": ConversationState.LOAD_PRESENTATION.value,
            "load": best_load,
            "message": self._format_load_presentation(best_load),
            "search_summary": search_results.get("search_summary", {}),
            "next_action": "await_response"
        }
    
    def handle_negotiation(self, call_id: str, carrier_ask: float) -> Dict[str, Any]:
        """Handle negotiation round with corrected broker logic."""
        conversation = self.conversations.get(call_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        # Check if load was presented
        presented_load = conversation["data"].get("presented_load")
        if not presented_load:
            return {
                "call_id": call_id,
                "state": ConversationState.FAILED.value,
                "outcome": "error",
                "message": "Please search for a load first before negotiating.",
                "next_action": "search_loads"
            }
        
        listed_rate = presented_load["total_rate"]
        
        conversation["negotiation_rounds"] += 1
        round_number = conversation["negotiation_rounds"]
        
        # Evaluate offer using corrected broker logic
        market_average = listed_rate  # Use our listed rate as market baseline
        broker_maximum = listed_rate * 1.20  # 20% above listed rate as walk-away point
        
        evaluation = self.negotiation_policy.evaluate_offer(
            listed_rate=listed_rate,
            carrier_ask=carrier_ask,  # Changed from 'offer' to 'carrier_ask'
            round_number=round_number,
            market_average=market_average,
            broker_maximum=broker_maximum  # Changed from 'broker_minimum'
        )
        
        conversation["data"]["last_carrier_ask"] = carrier_ask
        conversation["data"]["negotiation_history"] = conversation["data"].get("negotiation_history", [])
        conversation["data"]["negotiation_history"].append({
            "round": round_number,
            "carrier_ask": carrier_ask,
            "evaluation": evaluation
        })
        
        if evaluation["outcome"] == "accept":
            conversation["state"] = ConversationState.AGREEMENT
            conversation["data"]["final_rate"] = carrier_ask
            self._save_conversations()
            
            return {
                "call_id": call_id,
                "state": ConversationState.AGREEMENT.value,
                "outcome": "accepted",
                "final_rate": carrier_ask,
                "message": f"Perfect! I can accept your request of ${carrier_ask:,.2f}. Let me transfer you to our sales team to finalize the paperwork.",
                "next_action": "transfer_to_sales"
            }
        
        elif evaluation["outcome"] == "counter":
            conversation["state"] = ConversationState.NEGOTIATION
            counter_offer = evaluation["counter_offer"]
            conversation["data"]["last_counter_offer"] = counter_offer
            self._save_conversations()
            
            # Simple message for counter offers
            message = f"I can move up to ${counter_offer:,.2f}. How does that work for you?"
            
            return {
                "call_id": call_id,
                "state": ConversationState.NEGOTIATION.value,
                "outcome": "counter",
                "counter_offer": counter_offer,
                "round": round_number,
                "max_rounds": evaluation["max_rounds"],
                "message": message_variations,
                "next_action": "await_counter_response"
            }
        
        else:  # reject - final round reached
            conversation["state"] = ConversationState.FAILED
            self._save_conversations()
            
            return {
                "call_id": call_id,
                "state": ConversationState.FAILED.value,
                "outcome": "rejected",
                "reason": evaluation["message"],
                "message": evaluation["message"],
                "next_action": "end_call"
            }
    
    def get_conversation_summary(self, call_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation data for persistence."""
        conversation = self.conversations.get(call_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        data = conversation["data"]
        
        return {
            "call_id": call_id,
            "final_state": conversation["state"].value if hasattr(conversation["state"], 'value') else str(conversation["state"]),
            "mc_number": data.get("mc_number"),
            "carrier_name": data.get("carrier_name"),
            "fmcsa_status": data.get("fmcsa_verification", {}).get("status"),
            "equipment_type": data.get("equipment_type"),
            "presented_load": data.get("presented_load"),
            "negotiation_rounds": conversation["negotiation_rounds"],
            "final_rate": data.get("final_rate"),
            "last_offer": data.get("last_offer"),
            "negotiation_history": data.get("negotiation_history", []),
            "outcome": self._determine_outcome(conversation),
            "sentiment": self._analyze_sentiment(conversation),
            "extracted_data": self._extract_structured_data(conversation)
        }
    
    def _format_load_presentation(self, load: Dict[str, Any]) -> str:
        """Format load details for presentation."""
        return (
            f"I found a great load for you! {load['commodity']} from {load['origin_city']}, {load['origin_state']} "
            f"to {load['destination_city']}, {load['destination_state']}. "
            f"Pickup {load['pickup_date'][:10]}, delivery {load['delivery_date'][:10]}. "
            f"{load['miles']:.0f} miles, {load['weight']:,.0f} pounds. "
            f"We're offering ${load['total_rate']:,.2f} total. Are you interested?"
        )
    
    def _determine_outcome(self, conversation: Dict[str, Any]) -> str:
        """Determine final call outcome."""
        state = conversation["state"]
        if state == ConversationState.AGREEMENT:
            return "accepted"
        elif state == ConversationState.FAILED:
            return "rejected" 
        elif state == ConversationState.FINAL_OFFER:
            return "final_offer_pending"
        elif state == ConversationState.TRANSFER:
            return "transferred"
        else:
            return "incomplete"
    
    def _analyze_sentiment(self, conversation: Dict[str, Any]) -> str:
        """Analyze conversation sentiment (simplified)."""
        # Simplified sentiment analysis based on outcome
        outcome = self._determine_outcome(conversation)
        if outcome == "accepted":
            return "positive"
        elif outcome == "rejected":
            return "negative"
        else:
            return "neutral"
    
    def _extract_structured_data(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data for reporting."""
        data = conversation["data"]
        return {
            "equipment_type": data.get("equipment_type"),
            "origin_preference": data.get("origin_preference"),
            "destination_preference": data.get("destination_preference"),
            "rate_sensitivity": self._calculate_rate_sensitivity(conversation),
            "negotiation_aggressiveness": self._calculate_negotiation_aggressiveness(conversation)
        }

    def handle_final_offer_response(self, call_id: str, carrier_response: str) -> Dict[str, Any]:
    """Handle carrier's response to our final maximum offer."""
    conversation = self.conversations.get(call_id)
    if not conversation:
        return {"error": "Conversation not found"}
    
    # Parse carrier response (accept/reject)
    if "yes" in carrier_response.lower() or "accept" in carrier_response.lower():
        # They accepted our final offer
        conversation["state"] = ConversationState.AGREEMENT
        final_rate = conversation["data"].get("final_offer")
        conversation["data"]["final_rate"] = final_rate
        self._save_conversations()
        
        return {
            "call_id": call_id,
            "state": ConversationState.AGREEMENT.value,
            "outcome": "accepted",
            "final_rate": final_rate,
            "message": f"Excellent! We have a deal at ${final_rate:,.2f}. Let me connect you with our dispatch team.",
            "next_action": "transfer_to_sales"
        }
    else:
        # They rejected our final offer
        conversation["state"] = ConversationState.FAILED
        self._save_conversations()
        
        return {
            "call_id": call_id,
            "state": ConversationState.FAILED.value,
            "outcome": "no_agreement",
            "message": "I understand. Thank you for your time, and please call back - we get new loads every day.",
            "next_action": "end_call"
        }
    
    def _calculate_rate_sensitivity(self, conversation: Dict[str, Any]) -> str:
        """Calculate how sensitive carrier is to rates."""
        rounds = conversation["negotiation_rounds"]
        if rounds == 0:
            return "unknown"
        elif rounds == 1:
            return "low"
        elif rounds <= 2:
            return "medium"
        else:
            return "high"
    
    def _calculate_negotiation_aggressiveness(self, conversation: Dict[str, Any]) -> str:
        """Calculate negotiation aggressiveness."""
        history = conversation["data"].get("negotiation_history", [])
        if not history:
            return "unknown"
        
        # Analyze gap between offers and listed rate
        first_offer = history[0]["carrier_offer"]
        presented_load = conversation["data"].get("presented_load")
        if not presented_load:
            return "unknown"
            
        listed_rate = presented_load["total_rate"]
        gap_percentage = (listed_rate - first_offer) / listed_rate * 100
        
        if gap_percentage > 15:
            return "aggressive"
        elif gap_percentage > 5:
            return "moderate"
        else:
            return "conservative"
    
    def _save_mc_verification_to_db(self, call_id: str, mc_number: str, verification: Dict[str, Any]) -> None:
        """Save MC verification status to the Call database record."""
        try:
            from api.models import Call
            
            # Check if call record exists
            call = self.db.query(Call).filter(Call.call_id == call_id).first()
            
            if call:
                # Update existing call record
                call.carrier_mc = mc_number
                call.carrier_name = verification.get("carrier_name")
                call.fmcsa_status = "verified" if verification.get("eligible") else "failed"
            else:
                # Create new call record
                call = Call(
                    call_id=call_id,
                    carrier_mc=mc_number,
                    carrier_name=verification.get("carrier_name"),
                    fmcsa_status="verified" if verification.get("eligible") else "failed",
                    outcome="incomplete"  # Default outcome until call is completed
                )
                self.db.add(call)
            
            # Commit the changes
            self.db.commit()
            
        except Exception as e:
            # Log error but don't fail the verification process
            self.logger.warning(f"Failed to save MC verification to database: {str(e)}")
            self.db.rollback()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _create_no_match_message(self, equipment_type, origin_city, origin_state, 
                           destination_city, destination_state) -> str:
        """Create a helpful message when no loads match."""
        # Check for alternative cities in the same state
        alternative_message = self._check_for_state_alternatives(
            equipment_type, origin_city, origin_state, destination_city, destination_state
        )
        
        if alternative_message:
            return alternative_message
        
        # Build location string
        location_str = self._build_location_string(
            origin_city, origin_state, destination_city, destination_state
        )
        
        equipment_str = f"{equipment_type} " if equipment_type else ""
        return (f"I don't have any {equipment_str}loads available {location_str} right now. "
                "Let me transfer you to our load planning team to see if we can find something "
                "in nearby areas or check for new loads coming in.")
    
    def _build_location_string(self, origin_city, origin_state, destination_city, destination_state) -> str:
        """Build a formatted location string from city and state parameters."""
        location_parts = []
        
        # Add origin
        if origin_city and origin_state:
            location_parts.append(f"from {origin_city}, {origin_state}")
        elif origin_state:
            location_parts.append(f"from {origin_state}")
        
        # Add destination
        if destination_city and destination_state:
            location_parts.append(f"to {destination_city}, {destination_state}")
        elif destination_state:
            location_parts.append(f"to {destination_state}")
        
        return " ".join(location_parts)
    
    def _check_for_state_alternatives(self, equipment_type, origin_city, origin_state, 
                                    destination_city, destination_state) -> Optional[str]:
        """Check if there are loads available in the same state but different city."""
        # Create a search request for state-only matches
        # We need to provide valid strings for required fields, but use a dummy city
        state_search_request = LoadSearchRequest(
            equipment_type=equipment_type,
            origin_city="",  # Empty string to search for any city in the state
            origin_state=origin_state,  # State normalization will happen in LoadSearchService
            destination_city=destination_city or "",
            destination_state=destination_state or "",
            limit=3
        )
        
        # Search for loads in the same state
        search_results = self.load_service.search_loads(state_search_request)
        loads = search_results.get("loads", [])
        
        if not loads:
            return None
        
        # Filter loads that are in the same state but different city
        alternative_loads = []
        for load in loads:
            origin_match = False
            dest_match = False
            
            # Check origin
            if origin_state and load["origin_state"].upper() == origin_state.upper():
                if not origin_city or load["origin_city"].lower() != origin_city.lower():
                    origin_match = True
            
            # Check destination  
            if destination_state and load["destination_state"].upper() == destination_state.upper():
                if not destination_city or load["destination_city"].lower() != destination_city.lower():
                    dest_match = True
            
            if origin_match or dest_match:
                alternative_loads.append(load)
        
        if not alternative_loads:
            return None
        
        # Create helpful message with alternatives
        best_alternative = alternative_loads[0]
        equipment_str = f"{equipment_type} " if equipment_type else ""
        
        # Build location-specific message
        if origin_city and origin_state and destination_city and destination_state:
            # Both origin and destination specified
            if (best_alternative["origin_state"].upper() == origin_state.upper() and 
                best_alternative["origin_city"].lower() != origin_city.lower()):
                return (f"I don't have any {equipment_str}loads from {origin_city}, {origin_state}, "
                       f"but I do have loads from {best_alternative['origin_city']}, {best_alternative['origin_state']} "
                       f"to {best_alternative['destination_city']}, {best_alternative['destination_state']}. "
                       f"Would you be interested in that route?")
            elif (best_alternative["destination_state"].upper() == destination_state.upper() and 
                  best_alternative["destination_city"].lower() != destination_city.lower()):
                return (f"I don't have any {equipment_str}loads to {destination_city}, {destination_state}, "
                       f"but I do have loads from {best_alternative['origin_city']}, {best_alternative['origin_state']} "
                       f"to {best_alternative['destination_city']}, {best_alternative['destination_state']}. "
                       f"Would you be interested in that route?")
        elif origin_city and origin_state:
            # Only origin specified
            if (best_alternative["origin_state"].upper() == origin_state.upper() and 
                best_alternative["origin_city"].lower() != origin_city.lower()):
                return (f"I don't have any {equipment_str}loads from {origin_city}, {origin_state}, "
                       f"but I do have loads from {best_alternative['origin_city']}, {best_alternative['origin_state']}. "
                       f"Would you be interested in those?")
        elif destination_city and destination_state:
            # Only destination specified
            if (best_alternative["destination_state"].upper() == destination_state.upper() and 
                best_alternative["destination_city"].lower() != destination_city.lower()):
                return (f"I don't have any {equipment_str}loads to {destination_city}, {destination_state}, "
                       f"but I do have loads to {best_alternative['destination_city']}, {best_alternative['destination_state']}. "
                       f"Would you be interested in those?")
        
        return None    