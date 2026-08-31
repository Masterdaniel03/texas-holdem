from engine.bot_strategy import HeuristicAgent, RandomAgent, HumanAgent
from engine.evaluator import run_match

if __name__ == "__main__":
    results = run_match(
        agent_by_name={
            "Marcus": HeuristicAgent(),
            "Daniel": HeuristicAgent(),
            "Rex": RandomAgent(),
            "Linus": HeuristicAgent(),
            "Robert": RandomAgent(),
        },
        starting_chips=1000,
        small_blind=10,     
        big_blind=20,
        max_bet=1000,
        num_hands=100,
    )
    print("\n===== RESULTS =====")
    print(f"Hands played: {results['hands_played']}")
    print(f"Final chips:  {results['final_chips']}")
    print(f"Total chips:  {results['total_chips']}")