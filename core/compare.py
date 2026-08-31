from itertools import combinations
from collections import Counter
from .card import Card, Rank, Suit


class HandEvaluator:
    @staticmethod
    def evaluate_5_card_hand(cards: list[Card]) -> tuple:
        ranks = sorted([c.rank.value for c in cards], reverse=True)
        suits = [c.suit for c in cards]

        is_flush = len(set(suits)) == 1


        rank_set = set(ranks)
        is_straight = False
        straight_high = 0

        if len(rank_set) == 5:
            if max(ranks) - min(ranks) == 4:
                is_straight = True
                straight_high = max(ranks)
            elif rank_set == {14, 2, 3, 4, 5}: # Wheel straight
                is_straight = True
                straight_high = 5

        counts = Counter(ranks)
        sorted_by_freq = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        freq_pattern = [item[1] for item in sorted_by_freq]
        freq_ranks = [item[0] for item in sorted_by_freq]

        # 9. Straight Flush
        if is_straight and is_flush:
            return (9, straight_high)

        # 8. Four of a Kind
        if freq_pattern == [4, 1]:
            return (8, freq_ranks[0], freq_ranks[1])

        # 7. Full House
        if freq_pattern == [3, 2]:
            return (7, freq_ranks[0], freq_ranks[1])

        # 6. Flush
        if is_flush:
            return (6, *ranks)

        # 5. Straight
        if is_straight:
            return (5, straight_high)

        # 4. Three of a Kind
        if freq_pattern == [3, 1, 1]:
            return (4, freq_ranks[0], freq_ranks[1], freq_ranks[2])

        # 3. Two Pair
        if freq_pattern == [2, 2, 1]:
            return (3, freq_ranks[0], freq_ranks[1], freq_ranks[2])

        # 2. One Pair
        if freq_pattern == [2, 1, 1, 1]:
            return (2, freq_ranks[0], freq_ranks[1], freq_ranks[2], freq_ranks[3])

        # 1. High Card
        return (1, *ranks)

    @classmethod
    def evaluate_7_cards(cls, seven_cards: list[Card]) -> tuple:
        best_score = (-1,)
        for five_card_combo in combinations(seven_cards, 5):
            score = cls.evaluate_5_card_hand(list(five_card_combo))
            if score > best_score:
                best_score = score
        return best_score