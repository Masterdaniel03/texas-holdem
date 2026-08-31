import random
from .card import Card, Rank, Suit

class Deck:
    def __init__(self):
        self.cards = self._build_deck()
        self.shuffle()
    def _build_deck(self) -> list[Card]:
        return [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, count=1):
        if count > len(self.cards):
            raise ValueError("Not enough cards left in the deck.")

        drawn_cards = [self.cards.pop() for _ in range(count)]
        return drawn_cards if count > 1 else drawn_cards[0]

    def reset(self):
        self.cards = self._build_deck()
        self.shuffle()

    def __len__(self):
        return len(self.cards)