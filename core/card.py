from enum import IntEnum

class Suit(IntEnum):
    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self) -> str:
        # icon
        suit_symbols = {Suit.CLUBS: '♣', Suit.DIAMONDS: '♦', Suit.HEARTS: '♥', Suit.SPADES: '♠'}
        rank_symbols = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        
        r_str = rank_symbols.get(self.rank.value, str(self.rank.value))
        return f"{r_str}{suit_symbols[self.suit]}"

    # compare
    def __lt__(self, other):
        return self.rank < other.rank
        
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))