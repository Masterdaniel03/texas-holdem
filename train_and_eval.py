import argparse
import time

from core.card import Card, Rank, Suit
from engine.abstraction import state_key
from engine.bot_strategy import CFRAgent, HeuristicAgent, RandomAgent
from engine.cfr_trainer import CFRTrainer
from engine.evaluator import run_match


def canonical_hands():
    return {
        "AA": [Card(Rank.ACE, Suit.CLUBS), Card(Rank.ACE, Suit.DIAMONDS)],
        "72o": [Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.TWO, Suit.HEARTS)],
    }


def report_strategy_convergence(trainer, previous):
    for label, hand in canonical_hands().items():
        key = state_key(hand, [], "")
        node = trainer.node_map.get(key)
        if node is None:
            print(f"  {label}: no sampled InfoSet yet")
            continue

        strategy = node.get_average_strategy()
        change = None
        if label in previous:
            change = sum(abs(now - old) for now, old in zip(strategy, previous[label]))
        rendered = ", ".join(f"{probability:.3f}" for probability in strategy)
        change_text = "n/a" if change is None else f"{change:.4f}"
        print(f"  {label} [fold, call, raise]: [{rendered}], L1 change: {change_text}")
        previous[label] = strategy


def main():
    parser = argparse.ArgumentParser(description="Train and benchmark the abstracted CFR policy.")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--hands", type=int, default=1000)
    parser.add_argument("--model", default="models/cfr_policy.pkl")
    args = parser.parse_args()
    if args.iterations < 1 or args.hands < 1:
        parser.error("--iterations and --hands must be positive.")

    trainer = CFRTrainer()
    previous_strategies = {}
    started = time.time()
    interval = max(1, args.iterations // 10)
    remaining = args.iterations
    while remaining:
        batch = min(interval, remaining)
        trainer.train(batch)
        remaining -= batch
        print(f"InfoSets discovered: {len(trainer.node_map)}")
        report_strategy_convergence(trainer, previous_strategies)

    trainer.save_model(args.model)
    print(f"Saved CFR policy to {args.model}")
    print(f"Training time: {time.time() - started:.2f}s")

    results = run_match(
        {
            "CFR": CFRAgent(args.model),
            "Heuristic": HeuristicAgent(),
            "Random": RandomAgent(),
        },
        starting_chips=1000,
        small_blind=10,
        big_blind=20,
        max_bet=1000,
        num_hands=args.hands,
        rebuy=True,
        quiet=True,
    )
    print(f"Benchmark hands played: {results['hands_played']}")
    for name, bb_per_100 in results["bb_per_100"].items():
        print(f"{name}: {bb_per_100:.2f} bb/100")


if __name__ == "__main__":
    main()
