from core.deck import Deck
from engine.bot_strategy import InfoSet
from engine.fast_eval import FastEvaluator

class CFRTrainer:
    def __init__(self):
        self.node_map = {}

    def train(self, iterations: int = 10000):
        print(f"Starting CFR training for {iterations} iterations...")
        
        for i in range(iterations):
            if i % 1000 == 0 and i > 0:
                print(f"Completed {i} hands... Memory holds {len(self.node_map)} InfoSets.")

            deck = Deck()
            deck.shuffle()  
            
            p0_hole = deck.draw(2)
            p1_hole = deck.draw(2)
            board = deck.draw(5)

            self.cfr(
                history="", 
                p0_hole=p0_hole, 
                p1_hole=p1_hole, 
                board=board,
                p0_prob=1.0, 
                p1_prob=1.0, 
                current_player=0
            )
        
        print(f"Training complete! Final memory size: {len(self.node_map)} InfoSets.")


    def cfr(self, history: str, p0_hole: list, p1_hole: list, board: list, 
            p0_prob: float, p1_prob: float, current_player: int) -> float:
       
        if self.is_terminal(history):
            return self.calculate_payoff(history, p0_hole, p1_hole, board)

        if history.count('r') >= 3:
            valid_actions = ["fold", "call"]
        else:
            valid_actions = ["fold", "call", "raise"]

        my_hole = p0_hole if current_player == 0 else p1_hole
        info_set_key = self.get_current_state_key(history, my_hole, board)
        
        if info_set_key not in self.node_map:
            # Dynamically set num_actions to 2 or 3!
            self.node_map[info_set_key] = InfoSet(info_set_key, num_actions=len(valid_actions))
        node = self.node_map[info_set_key]

        weight = p0_prob if current_player == 0 else p1_prob
        strategy = node.get_strategy(realization_weight=weight)

        action_values = [0.0] * node.num_actions
        node_value = 0.0

        for i, action in enumerate(valid_actions):
            if current_player == 0:
                action_values[i] = -self.cfr(history + action[0], p0_hole, p1_hole, board, 
                                             p0_prob * strategy[i], p1_prob, 1)
            else:
                action_values[i] = -self.cfr(history + action[0], p0_hole, p1_hole, board, 
                                             p0_prob, p1_prob * strategy[i], 0)
            
            node_value += strategy[i] * action_values[i]

        opponent_prob = p1_prob if current_player == 0 else p0_prob
        for i in range(node.num_actions):
            regret = action_values[i] - node_value
            node.regret_sum[i] += opponent_prob * regret

        return node_value
    
    def is_terminal(self, history: str) -> bool:
        if not history:
            return False

        if history[-1] == 'f':
            return True
            
        if history[-1] == 'c' and len(history) > 1:
            return True
            
        return False
        
    def calculate_payoff(self, history: str, p0_hole: list, p1_hole: list, board: list) -> float:
        current_player = len(history) % 2
        
        contributions = [1.0, 1.0]
        current_bet = 0.0
        acting_player = 0
        for ch in history:
            if ch == 'r':
                current_bet += 1.0
                contributions[acting_player] = 1.0 + current_bet
            elif ch == 'c':
                contributions[acting_player] = 1.0 + current_bet
            acting_player = 1 - acting_player

        pot = contributions[0] + contributions[1]
        net = [-contributions[0], -contributions[1]]

        if history[-1] == 'f':
            net[current_player] += pot
            return net[current_player]

        p0_score = FastEvaluator.get_best_hand(p0_hole, board)
        p1_score = FastEvaluator.get_best_hand(p1_hole, board)

        if p0_score < p1_score:
            net[0] += pot
        elif p1_score < p0_score:
            net[1] += pot
        else:
            net[0] += pot / 2.0
            net[1] += pot / 2.0

        return net[current_player]         
        
    def get_current_state_key(self, history: str, hole_cards: list, board: list) -> str:

        sorted_cards = sorted(hole_cards, key=lambda c: c.rank.value, reverse=True)

        hole_str = "".join([FastEvaluator._convert_card(c) for c in sorted_cards])
        
        return f"{hole_str}_{history}"

    