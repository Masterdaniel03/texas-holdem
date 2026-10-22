from collections import Counter
from typing import Optional

from core.card import Card
from engine.fast_eval import FastEvaluator


RANK_SYMBOLS = {
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}

STREETS = ("preflop", "flop", "turn", "river")
BOARD_SIZES = (0, 3, 4, 5)


def _rank_symbol(card: Card) -> str:
    return RANK_SYMBOLS.get(card.rank.value, str(card.rank.value))


def canonical_preflop_hand(hole_cards: list[Card]) -> str:
    """Return one of the 169 rank-ordered starting-hand classes."""
    if len(hole_cards) != 2:
        raise ValueError("Preflop abstraction requires exactly two hole cards.")

    high, low = sorted(hole_cards, key=lambda card: card.rank.value, reverse=True)
    ranks = f"{_rank_symbol(high)}{_rank_symbol(low)}"
    if high.rank == low.rank:
        return ranks
    return f"{ranks}{'s' if high.suit == low.suit else 'o'}"


def street_for_board(board: list[Card]) -> str:
    if len(board) == 0:
        return STREETS[0]
    if len(board) <= 3:
        return STREETS[1]
    if len(board) == 4:
        return STREETS[2]
    return STREETS[3]


def _board_texture(board: list[Card]) -> str:
    ranks = [card.rank.value for card in board]
    suits = Counter(card.suit for card in board)
    paired = "paired" if len(set(ranks)) < len(ranks) else "unpaired"
    max_suit_count = max(suits.values(), default=0)

    if len(board) == 3 and max_suit_count == 3:
        flush_texture = "mono"
    elif len(board) == 3 and max_suit_count == 2:
        flush_texture = "draw"
    elif len(board) == 4 and max_suit_count >= 3:
        flush_texture = "draw"
    elif len(board) == 5 and max_suit_count >= 3:
        flush_texture = "flush"
    elif max_suit_count == 2:
        flush_texture = "two-tone"
    else:
        flush_texture = "rainbow"
    return f"{paired}-{flush_texture}"


def postflop_bucket(hole_cards: list[Card], board: list[Card]) -> str:
    if len(hole_cards) != 2:
        raise ValueError("Postflop abstraction requires exactly two hole cards.")
    if len(board) not in (3, 4, 5):
        raise ValueError("Postflop abstraction requires a flop, turn, or river board.")

    # phevaluator scores are ordered with lower values representing stronger hands.
    score = FastEvaluator.get_best_hand(hole_cards, board)
    strength_bucket = 9 - min(9, max(0, (score - 1) * 10 // 7462))
    return f"b{strength_bucket}-{_board_texture(board)}"


def abstract_hand(hole_cards: list[Card], board: list[Card]) -> tuple[str, str]:
    street = street_for_board(board)
    if street == "preflop":
        return street, canonical_preflop_hand(hole_cards)
    return street, postflop_bucket(hole_cards, board)


def state_key(
    hole_cards: list[Card],
    board: list[Card],
    bet_history: str,
    street: Optional[str] = None,
) -> str:
    """Format the shared trainer/live-agent key as street:bucket:history."""
    inferred_street, hand_bucket = abstract_hand(hole_cards, board)
    street = street or inferred_street
    if street not in STREETS:
        raise ValueError(f"Unknown poker street: {street}")
    return f"{street}:{hand_bucket}:{bet_history}"
