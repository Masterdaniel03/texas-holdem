import contextlib
import os

from core.game import GameEngine
from core.player import Player


def run_match(agent_by_name: dict, starting_chips: int = 1000,
              small_blind: int = 10, big_blind: int = 20, max_bet: int = 10_000,
              num_hands: int = 200, rebuy: bool = False, quiet: bool = False) -> dict:
    players = [Player(name, starting_chips) for name in agent_by_name]
    agents = {p: agent_by_name[p.name] for p in players}
    engine = GameEngine(players, agents)

    hands_played = 0
    rebuys = {player.name: 0 for player in players}
    for _ in range(num_hands):
        if rebuy:
            for player in players:
                if player.chips <= 0:
                    player.chips = starting_chips
                    rebuys[player.name] += 1
        if sum(1 for p in players if p.chips > 0) <= 1:
            break
        if quiet:
            with open(os.devnull, "w", encoding="utf-8") as sink, contextlib.redirect_stdout(sink):
                engine.play_hand(small_blind, big_blind, max_bet)
        else:
            engine.play_hand(small_blind, big_blind, max_bet)
        hands_played += 1

    net_chips = {
        player.name: player.chips - starting_chips - rebuys[player.name] * starting_chips
        for player in players
    }
    hands_denominator = hands_played / 100.0
    bb_per_100 = {
        name: (net / big_blind / hands_denominator) if hands_denominator else 0.0
        for name, net in net_chips.items()
    }
    return {
        "hands_played": hands_played,
        "final_chips": {p.name: p.chips for p in players},
        "total_chips": sum(p.chips for p in players),
        "rebuys": rebuys,
        "net_chips": net_chips,
        "bb_per_100": bb_per_100,
    }


if __name__ == "__main__":
    from engine.bot_strategy import HeuristicAgent, RandomAgent

    results = run_match({
        "Alice": HeuristicAgent(),
        "Bob": HeuristicAgent(),
        "Carol": RandomAgent(),
        "Dave": HeuristicAgent(),
        "Eve": RandomAgent(),
    }, num_hands=200)

    print(results)