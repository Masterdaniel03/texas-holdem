import os
import pickle

from core.deck import Deck
from engine.abstraction import BOARD_SIZES, state_key
from engine.bot_strategy import InfoSet
from engine.fast_eval import FastEvaluator


class CFRTrainer:
    MAX_RAISES_PER_STREET = 2

    def __init__(self):
        self.node_map: dict[str, InfoSet] = {}

    def train(self, iterations: int = 10000):
        print(f"Starting CFR training for {iterations} iterations...")

        for iteration in range(iterations):
            if iteration > 0 and iteration % 1000 == 0:
                print(
                    f"Completed {iteration} hands... "
                    f"Memory holds {len(self.node_map)} InfoSets."
                )

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
                current_player=0,
                contributions=(0.5, 1.0),
                round_bets=(0.5, 1.0),
                current_bet=1.0,
            )

        print(f"Training complete! Final memory size: {len(self.node_map)} InfoSets.")

    def cfr(
        self,
        history: str,
        p0_hole: list,
        p1_hole: list,
        board: list,
        p0_prob: float,
        p1_prob: float,
        current_player: int,
        contributions: tuple[float, float] = (0.0, 0.0),
        round_bets: tuple[float, float] = (0.0, 0.0),
        current_bet: float = 0.0,
    ) -> float:
        """Return utility from player 0's perspective for the sampled hand."""
        current_street_history = history.rsplit("/", 1)[-1]
        raises_this_street = current_street_history.count("r")
        visible_board = self._visible_board(history, board)

        if self._is_showdown(history, current_street_history):
            return self._showdown_payoff(p0_hole, p1_hole, board, contributions)

        actions = ["fold", "call"]
        if raises_this_street < self.MAX_RAISES_PER_STREET:
            actions.append("raise")

        my_hole = p0_hole if current_player == 0 else p1_hole
        info_set_key = state_key(my_hole, visible_board, history)
        node = self.node_map.get(info_set_key)
        if node is None:
            node = InfoSet(info_set_key, num_actions=len(actions))
            self.node_map[info_set_key] = node

        reach_probability = p0_prob if current_player == 0 else p1_prob
        strategy = node.get_strategy(realization_weight=reach_probability)
        action_values = [0.0] * len(actions)
        node_value = 0.0

        for index, action in enumerate(actions):
            next_history = history + action[0]
            next_contributions = list(contributions)
            next_round_bets = list(round_bets)
            next_current_bet = current_bet

            if action == "fold":
                child_value = self._fold_payoff(
                    current_player, contributions
                )
            else:
                if action == "raise":
                    next_current_bet = current_bet + 1.0
                amount_owed = max(0.0, next_current_bet - next_round_bets[current_player])
                next_contributions[current_player] += amount_owed
                next_round_bets[current_player] += amount_owed

                round_closed = action == "call" and (
                    current_street_history.endswith("r")
                    or current_street_history.endswith("c")
                )
                if round_closed and history.count("/") == 3:
                    child_value = self._showdown_payoff(
                        p0_hole,
                        p1_hole,
                        board,
                        tuple(next_contributions),
                    )
                elif round_closed:
                    next_history += "/"
                    child_value = self.cfr(
                        history=next_history,
                        p0_hole=p0_hole,
                        p1_hole=p1_hole,
                        board=board,
                        p0_prob=p0_prob * strategy[index] if current_player == 0 else p0_prob,
                        p1_prob=p1_prob * strategy[index] if current_player == 1 else p1_prob,
                        current_player=1,
                        contributions=tuple(next_contributions),
                        round_bets=(0.0, 0.0),
                        current_bet=0.0,
                    )
                else:
                    child_value = self.cfr(
                        history=next_history,
                        p0_hole=p0_hole,
                        p1_hole=p1_hole,
                        board=board,
                        p0_prob=p0_prob * strategy[index] if current_player == 0 else p0_prob,
                        p1_prob=p1_prob * strategy[index] if current_player == 1 else p1_prob,
                        current_player=1 - current_player,
                        contributions=tuple(next_contributions),
                        round_bets=tuple(next_round_bets),
                        current_bet=next_current_bet,
                    )

            action_values[index] = child_value
            node_value += strategy[index] * child_value

        opponent_probability = p1_prob if current_player == 0 else p0_prob
        for index, action_value in enumerate(action_values):
            regret = (
                action_value - node_value
                if current_player == 0
                else node_value - action_value
            )
            node.regret_sum[index] += opponent_probability * regret

        return node_value

    @staticmethod
    def _visible_board(history: str, board: list) -> list:
        street_index = min(history.count("/"), len(BOARD_SIZES) - 1)
        return board[:BOARD_SIZES[street_index]]

    @staticmethod
    def _is_showdown(history: str, current_street_history: str) -> bool:
        return (
            history.count("/") == 3
            and current_street_history.endswith("c")
            and (
                len(current_street_history) >= 2
                and current_street_history[-2] in ("r", "c")
            )
        )

    @staticmethod
    def _fold_payoff(current_player: int, contributions: tuple[float, float]) -> float:
        pot = sum(contributions)
        winner = 1 - current_player
        net = [-contributions[0], -contributions[1]]
        net[winner] += pot
        return net[0]

    @staticmethod
    def _showdown_payoff(
        p0_hole: list,
        p1_hole: list,
        board: list,
        contributions: tuple[float, float],
    ) -> float:
        p0_score = FastEvaluator.get_best_hand(p0_hole, board[:5])
        p1_score = FastEvaluator.get_best_hand(p1_hole, board[:5])
        pot = sum(contributions)
        net = [-contributions[0], -contributions[1]]
        if p0_score < p1_score:
            net[0] += pot
        elif p1_score < p0_score:
            net[1] += pot
        else:
            net[0] += pot / 2.0
            net[1] += pot / 2.0
        return net[0]

    def is_terminal(self, history: str) -> bool:
        if not history:
            return False
        last_street = history.rsplit("/", 1)[-1]
        if last_street.endswith("f"):
            return True
        return history.count("/") == 3 and self._is_showdown(history, last_street)

    def calculate_payoff(self, history: str, p0_hole: list, p1_hole: list, board: list) -> float:
        """Compatibility helper for evaluating a terminal history without state arguments."""
        contributions = [0.5, 1.0]
        for street_index, street_history in enumerate(history.split("/")):
            round_bets = [0.5, 1.0] if street_index == 0 else [0.0, 0.0]
            current_bet = max(round_bets)
            player = 0 if street_index == 0 else 1
            for action in street_history:
                if action == "f":
                    return self._fold_payoff(player, tuple(contributions))
                if action == "r":
                    current_bet += 1.0
                amount = max(0.0, current_bet - round_bets[player])
                contributions[player] += amount
                round_bets[player] += amount
                player = 1 - player

        return self._showdown_payoff(
            p0_hole, p1_hole, board, tuple(contributions)
        )

    def get_current_state_key(self, history: str, hole_cards: list, board: list) -> str:
        visible_board = self._visible_board(history, board)
        return state_key(hole_cards, visible_board, history)

    def save_model(self, filepath: str) -> None:
        directory = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(directory, exist_ok=True)
        payload = {
            key: {
                "num_actions": node.num_actions,
                "regret_sum": list(node.regret_sum),
                "strategy_sum": list(node.strategy_sum),
            }
            for key, node in self.node_map.items()
        }
        with open(filepath, "wb") as model_file:
            pickle.dump(payload, model_file, protocol=pickle.HIGHEST_PROTOCOL)

    def load_model(self, filepath: str) -> dict[str, InfoSet]:
        with open(filepath, "rb") as model_file:
            payload = pickle.load(model_file)
        if not isinstance(payload, dict):
            raise ValueError("CFR model must contain a dictionary of information sets.")

        loaded: dict[str, InfoSet] = {}
        for key, values in payload.items():
            if not isinstance(key, str) or not isinstance(values, dict):
                raise ValueError("CFR model contains an invalid information set.")
            num_actions = values.get("num_actions")
            regrets = values.get("regret_sum")
            strategy_sums = values.get("strategy_sum")
            if (
                not isinstance(num_actions, int)
                or num_actions <= 0
                or not isinstance(regrets, list)
                or not isinstance(strategy_sums, list)
                or len(regrets) != num_actions
                or len(strategy_sums) != num_actions
            ):
                raise ValueError(f"CFR model contains invalid data for {key!r}.")
            node = InfoSet(key, num_actions=num_actions)
            node.regret_sum = regrets
            node.strategy_sum = strategy_sums
            loaded[key] = node

        self.node_map = loaded
        return self.node_map
