class Player:
    def __init__(self, name: str, starting_chips: int):
        self.name = name
        self.chips = starting_chips
        self.hand = []
        self.is_active = True          
        self.current_round_bet = 0    
        self.total_bet_this_hand = 0 

    def receive_cards(self, cards):
        self.hand.extend(cards)

    def bet(self, amount: int) -> int:
        if amount < 0:
            amount = 0
        if amount > self.chips:
            amount = self.chips
        self.chips -= amount
        self.current_round_bet += amount
        self.total_bet_this_hand += amount
        return amount

    def fold(self):
        self.is_active = False

    def reset_hand(self):
        self.hand = []
        self.is_active = True
        self.current_round_bet = 0
        self.total_bet_this_hand = 0

    def reset_round_bet(self):
        self.current_round_bet = 0

    @property
    def is_all_in(self) -> bool:
        return self.is_active and self.chips == 0