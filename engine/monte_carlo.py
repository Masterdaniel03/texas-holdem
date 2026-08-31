# engine/monte_carlo.py
import random
from math import comb
from core.card import Card
from core.deck import Deck
from engine.fast_eval import FastEvaluator 


def estimate_equity(hero_hand: list[Card], community_cards: list[Card],
                     num_opponents: int, trials: int = 300) -> float:
    known = set(hero_hand) | set(community_cards)
    remaining = [c for c in Deck().cards if c not in known]

    cards_needed = num_opponents * 2 + (5 - len(community_cards))
    if cards_needed > len(remaining):
        return 0.0

    trials_run = min(trials, comb(len(remaining), cards_needed))

    wins = 0.0
    for _ in range(trials_run):
        sample = random.sample(remaining, cards_needed)
        opp_holes = [sample[i * 2:i * 2 + 2] for i in range(num_opponents)]
        board = community_cards + sample[2 * num_opponents:]

        my_score = FastEvaluator.get_best_hand(hero_hand, board)
        opp_scores = [FastEvaluator.get_best_hand(h, board) for h in opp_holes]

        best_opp = min(opp_scores)
        if my_score < best_opp:
            wins += 1.0
        elif my_score == best_opp:
            wins += 1.0 / (1 + sum(1 for s in opp_scores if s == best_opp))

    return wins / trials_run if trials_run else 0.0