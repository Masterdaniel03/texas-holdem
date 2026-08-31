from core.game import GameEngine
from core.player import Player


def run_match(agent_by_name: dict, starting_chips: int = 1000,
              small_blind: int = 10, big_blind: int = 20, max_bet: int = 10_000,
              num_hands: int = 200) -> dict:
    
    players = [Player(name, starting_chips) for name in agent_by_name]
    agents = {p: agent_by_name[p.name] for p in players}
    engine = GameEngine(players, agents)

    hands_played = 0
    for _ in range(num_hands):
        if sum(1 for p in players if p.chips > 0) <= 1:
            break
        engine.play_hand(small_blind, big_blind, max_bet)
        hands_played += 1

    return {
        "hands_played": hands_played,
        "final_chips": {p.name: p.chips for p in players},
        "total_chips": sum(p.chips for p in players),
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