from .deck import Deck
from .player import Player
from .compare import HandEvaluator


class GameEngine:
    def __init__(self, players: list[Player], agents: dict):
        self.deck = Deck()
        self.players = players
        self.agents = agents
        self.pot = 0
        self.community_cards = []
        self.current_bet = 0
        self.button_index = -1

    # ---------- pot ----------

    def place_bet(self, player, amount: int) -> int:
        bet_amount = player.bet(amount)
        self.pot += bet_amount
        return bet_amount

    def is_hand_over(self) -> bool:
        return sum(1 for p in self.players if p.is_active) <= 1

    # ---------- hand setup ----------

    def start_round(self):
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.button_index = (self.button_index + 1) % len(self.players)

        for player in self.players:
            player.reset_hand()
            if player.chips <= 0:
                player.is_active = False  

        for player in self.players:
            if player.is_active:
                player.receive_cards(self.deck.draw(2))
        for player in self.players:
            if player.is_active:
                print(f"{player.name}'s Hole Cards: {player.hand}")
        print()

    def post_blinds(self, small_blind: int, big_blind: int):
        n = len(self.players)
        if n == 2:
            sb_index, bb_index = self.button_index, (self.button_index + 1) % n
        else:
            sb_index = (self.button_index + 1) % n
            bb_index = (self.button_index + 2) % n

        sb_player, bb_player = self.players[sb_index], self.players[bb_index]
        sb_posted = self.place_bet(sb_player, small_blind)
        bb_posted = self.place_bet(bb_player, big_blind)
        self.current_bet = big_blind

        print(f"{sb_player.name} posts small blind ({sb_posted})")
        print(f"{bb_player.name} posts big blind ({bb_posted})\n")

    def preflop_first_to_act(self) -> int:
        n = len(self.players)
        return self.button_index if n == 2 else (self.button_index + 3) % n

    def postflop_first_to_act(self) -> int:
        return (self.button_index + 1) % len(self.players)

    # ---------- board ----------

    def deal_flop(self):
        self.deck.draw(1)
        self.community_cards.extend(self.deck.draw(3))

    def deal_turn_or_river(self):
        self.deck.draw(1)
        self.community_cards.append(self.deck.draw(1))

    # ---------- betting ----------

    def _seats_from(self, start_index: int):
        n = len(self.players)
        seats = [self.players[(start_index + i) % n] for i in range(n)]
        return [p for p in seats if p.is_active]

    def execute_betting_round(self, big_blind: int, max_bet: int,
                               first_to_act_index: int, is_preflop: bool = False):
        last_raise = big_blind

        if not is_preflop:
            self.current_bet = 0
            for player in self.players:
                if player.is_active:
                    player.reset_round_bet()

        print(f"Community Board: {self.community_cards}\n")

        queue = [p for p in self._seats_from(first_to_act_index) if p.chips > 0]

        while queue:
            if self.is_hand_over():
                break
            if len([p for p in self.players if p.is_active and p.chips > 0]) <= 1:
                break  # everyone else is all-in or folded — no more decisions possible

            player = queue.pop(0)
            if not player.is_active or player.chips == 0:
                continue  # folded or busted since being queued

            owed = self.current_bet - player.current_round_bet
            valid_actions = ["fold", "check" if owed <= 0 else "call"]
            if player.chips > owed and self.current_bet < max_bet:
                valid_actions.append("raise")
            min_legal_raise = self.current_bet + last_raise
            context = {
                "owed": owed,
                "pot": self.pot,
                "current_bet": self.current_bet,
                "min_raise_to": min_legal_raise,
                "max_bet": max_bet,
            }

            action, requested_raise_to = self.agents[player].decide(self, player, valid_actions, context)

            if action not in valid_actions:
                queue.insert(0, player)
                continue

            if action == "fold":
                player.fold()
                print(f"{player.name} folds")

            elif action == "call":
                self.place_bet(player, owed)
                print(f"{player.name} calls ({owed})")

            elif action == "raise":
                raise_amount = requested_raise_to if requested_raise_to is not None else min_legal_raise
                raise_amount = max(min_legal_raise, raise_amount)
                raise_amount = min(raise_amount, max_bet, player.current_round_bet + player.chips)

                if (raise_amount - self.current_bet) >= last_raise:
                    last_raise = raise_amount - self.current_bet  # only a FULL raise resets the min-raise size

                self.place_bet(player, raise_amount - player.current_round_bet)
                self.current_bet = raise_amount
                print(f"{player.name} raises to {raise_amount}")

                queue = [p for p in self._seats_from((self.players.index(player) + 1) % len(self.players))
                         if p.is_active and p.chips > 0 and p is not player]

    # ---------- showdown ----------

    def determine_winner(self):
        contenders = [p for p in self.players if p.total_bet_this_hand > 0]
        if not contenders:
            print("No chips were bet this hand.")
            return

        levels = sorted(set(p.total_bet_this_hand for p in contenders))
        pots, previous_level = [], 0
        for level in levels:
            layer_players = [p for p in contenders if p.total_bet_this_hand >= level]
            layer_amount = (level - previous_level) * len(layer_players)
            eligible = [p for p in layer_players if p.is_active]
            if layer_amount > 0:
                pots.append((layer_amount, eligible))
            previous_level = level

        total_paid_out = 0
        for pot_amount, eligible_players in pots:
            if not eligible_players:
                continue

            if len(eligible_players) == 1:
                winners, best_score = eligible_players, None  # walkover — no showdown needed
            else:
                best_score, winners = (-1,), []
                for player in eligible_players:
                    score = HandEvaluator.evaluate_7_cards(player.hand + self.community_cards)
                    if score > best_score:
                        best_score, winners = score, [player]
                    elif score == best_score:
                        winners.append(player)

            split, remainder = divmod(pot_amount, len(winners))
            label = f"score {best_score}" if best_score is not None else "no showdown needed"
            print(f"Pot of {pot_amount} ({label}): " +
                  ", ".join(f"{w.name} wins {split + (1 if i < remainder else 0)}"
                            for i, w in enumerate(winners)))
            for i, winner in enumerate(winners):
                winner.chips += split + (1 if i < remainder else 0)
            total_paid_out += pot_amount

        assert total_paid_out == self.pot, "Chip conservation violated in payout!"
        self.pot = 0

    # ---------- full hand ----------

    def play_hand(self, small_blind: int, big_blind: int, max_bet: int):
        
        self.start_round()
        self.post_blinds(small_blind, big_blind)
        self.execute_betting_round(big_blind, max_bet, self.preflop_first_to_act(), is_preflop=True)

        for deal_street in (self.deal_flop, self.deal_turn_or_river, self.deal_turn_or_river):
            if self.is_hand_over():
                break
            deal_street()
            if sum(1 for p in self.players if p.is_active and p.chips > 0) > 1:
                self.execute_betting_round(big_blind, max_bet, self.postflop_first_to_act())

        self.determine_winner()