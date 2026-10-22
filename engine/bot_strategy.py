import random
from abc import ABC, abstractmethod

from engine.abstraction import state_key
from engine.monte_carlo import estimate_equity


class Agent(ABC):
    @abstractmethod
    def decide(self, game, player, valid_actions, context):
        ...


class HumanAgent(Agent):

    def decide(self, game, player, valid_actions, context):
        action = input(
            f"{player.name}'s turn. Hand: {player.hand}. Valid actions: {valid_actions}. "
            f"Current bet: {context['current_bet']}. Enter action: "
        ).strip().lower()

        raise_to = None
        if action == "raise":
            raise_to = int(input(
                f"Enter raise amount (min {context['min_raise_to']}, max {context['max_bet']}): "
            ))
        return action, raise_to


class RandomAgent(Agent):

    def decide(self, game, player, valid_actions, context):
        action = random.choice(valid_actions)
        raise_to = None
        if action == "raise":
            hi = min(context["max_bet"], player.current_round_bet + player.chips)
            raise_to = random.randint(context["min_raise_to"], max(context["min_raise_to"], hi))
        return action, raise_to


class HeuristicAgent(Agent):

    def __init__(self, trials: int = 300, raise_threshold: float = 0.62, bluff_rate: float = 0.05):
        self.trials = trials
        self.raise_threshold = raise_threshold
        self.bluff_rate = bluff_rate

    def decide(self, game, player, valid_actions, context):
        num_opponents = sum(1 for p in game.players if p.is_active and p is not player)
        equity = estimate_equity(player.hand, game.community_cards, num_opponents, self.trials)

        owed = context["owed"]
        pot_odds = owed / (context["pot"] + owed) if owed > 0 else 0.0
        bluffing = random.random() < self.bluff_rate

        if "raise" in valid_actions and (equity >= self.raise_threshold or bluffing):
            size = int(context["pot"] * 0.75) + context["current_bet"]
            return "raise", max(context["min_raise_to"], size)

        if owed <= 0:
            return "check", None

        if equity >= pot_odds or bluffing:
            return "call", None

        return "fold", None


class InfoSet:
    def __init__(self, key: str, num_actions: int = 3):
        self.key = key 
        self.num_actions = num_actions
        
        self.regret_sum = [0.0] * num_actions      
        self.strategy_sum = [0.0] * num_actions
        self.strategy = [1.0 / num_actions] * num_actions  


    def get_strategy(self, realization_weight: float) -> list[float]:
        normalizing_sum = 0.0
        for i in range(self.num_actions):
            self.strategy[i] = max(self.regret_sum[i], 0.0)
            normalizing_sum += self.strategy[i]

        for i in range(self.num_actions):
            self.strategy[i] = self.strategy[i] / normalizing_sum if normalizing_sum > 0 else 1.0 / self.num_actions
            self.strategy_sum[i] += realization_weight * self.strategy[i]

        return self.strategy

    def get_average_strategy(self) -> list[float]:
        avg_strategy = [0.0] * self.num_actions
        normalizing_sum = sum(self.strategy_sum)
        
        if normalizing_sum > 0:
            for i in range(self.num_actions):
                avg_strategy[i] = self.strategy_sum[i] / normalizing_sum
        else:
            for i in range(self.num_actions):
                avg_strategy[i] = 1.0 / self.num_actions
                
        return avg_strategy


class CFRAgent(Agent):
    def __init__(self, model_path: str = None):
        self.node_map = {}
        self.fallback_agent = HeuristicAgent()
        if model_path is not None:
            from engine.cfr_trainer import CFRTrainer

            self.node_map = CFRTrainer().load_model(model_path)

    def decide(self, game, player, valid_actions, context):
        history = getattr(game, "bet_history", "")
        street = getattr(game, "current_street", None)
        info_set_key = state_key(
            player.hand,
            game.community_cards,
            history,
            street=street,
        )
        node = self.node_map.get(info_set_key)
        if node is None:
            return self.fallback_agent.decide(game, player, valid_actions, context)

        strategy = node.get_average_strategy()
        available_indices = []
        action_names = []
        if "fold" in valid_actions and len(strategy) > 0:
            available_indices.append(0)
            action_names.append("fold")
        if len(strategy) > 1:
            check_call = "check" if "check" in valid_actions else "call"
            if check_call in valid_actions:
                available_indices.append(1)
                action_names.append(check_call)
        if "raise" in valid_actions and len(strategy) > 2:
            available_indices.append(2)
            action_names.append("raise")

        if not available_indices:
            return self.fallback_agent.decide(game, player, valid_actions, context)

        probabilities = [strategy[index] for index in available_indices]
        total_probability = sum(probabilities)
        if total_probability <= 0:
            probabilities = [1.0 / len(available_indices)] * len(available_indices)
        else:
            probabilities = [probability / total_probability for probability in probabilities]
        action = random.choices(action_names, weights=probabilities, k=1)[0]

        if action == "raise":
            size = max(
                context["min_raise_to"],
                int(context["pot"] * 0.75) + context["current_bet"],
            )
            return action, min(size, context["max_bet"])
        return action, None