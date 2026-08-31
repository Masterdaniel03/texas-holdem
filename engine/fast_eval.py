# engine/fast_eval.py
from phevaluator.evaluator import evaluate_cards
from core.card import Card 

class FastEvaluator:
    @staticmethod
    def _convert_card(your_card: Card) -> str:
        rank_map = {10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        rank_str = rank_map.get(your_card.rank.value, str(your_card.rank.value))
        suit_str = your_card.suit.name[0].lower() 
        return f"{rank_str}{suit_str}"

    @classmethod
    def get_best_hand(cls, hole_cards: list[Card], community_cards: list[Card]) -> int:
        cards = [cls._convert_card(c) for c in hole_cards + community_cards]
        return evaluate_cards(*cards)