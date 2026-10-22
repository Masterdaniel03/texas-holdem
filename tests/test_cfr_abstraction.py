import itertools

from core.card import Card, Rank, Suit
from core.deck import Deck
from core.player import Player
from engine.abstraction import canonical_preflop_hand, postflop_bucket, state_key
from engine.bot_strategy import CFRAgent, InfoSet
from engine.cfr_trainer import CFRTrainer


def test_preflop_abstraction_has_169_canonical_hands():
    hands = {
        canonical_preflop_hand(list(cards))
        for cards in itertools.combinations(Deck().cards, 2)
    }

    assert len(hands) == 169
    assert "AA" in hands
    assert "AKs" in hands
    assert "72o" in hands


def test_state_key_uses_shared_abstraction_and_street_history():
    hand = [Card(Rank.ACE, Suit.CLUBS), Card(Rank.KING, Suit.CLUBS)]
    equivalent_hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS)]

    assert state_key(hand, [], "r") == "preflop:AKs:r"
    assert state_key(hand, [], "r") == state_key(equivalent_hand, [], "r")


def test_postflop_bucket_includes_rank_strength_and_board_texture():
    hand = [Card(Rank.ACE, Suit.CLUBS), Card(Rank.KING, Suit.DIAMONDS)]
    board = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.DIAMONDS),
        Card(Rank.NINE, Suit.HEARTS),
    ]

    assert postflop_bucket(hand, board).startswith("b")
    assert postflop_bucket(hand, board).endswith("unpaired-rainbow")


def test_trainer_visibly_advances_board_and_detects_terminal_states():
    trainer = CFRTrainer()
    board = Deck().draw(5)

    assert len(trainer._visible_board("r", board)) == 0
    assert len(trainer._visible_board("r/cc", board)) == 3
    assert len(trainer._visible_board("r/cc/r", board)) == 4
    assert len(trainer._visible_board("r/cc/r/cc", board)) == 5
    assert trainer.is_terminal("cc/cc/cc/cc")
    assert trainer.is_terminal("rc/cc/f")
    assert not trainer.is_terminal("cc/cc/cc")


def test_training_discovers_information_sets_on_all_streets(capsys):
    trainer = CFRTrainer()
    trainer.train(1)

    streets = {key.split(":", 1)[0] for key in trainer.node_map}
    assert streets == {"preflop", "flop", "turn", "river"}
    capsys.readouterr()


def test_cfr_agent_samples_learned_action_from_shared_state_key(tmp_path):
    hand = [Card(Rank.ACE, Suit.CLUBS), Card(Rank.ACE, Suit.DIAMONDS)]
    key = state_key(hand, [], "")
    node = InfoSet(key)
    node.strategy_sum = [0.0, 1.0, 0.0]
    trainer = CFRTrainer()
    trainer.node_map[key] = node
    model_path = tmp_path / "policy.pkl"
    trainer.save_model(str(model_path))

    class GameState:
        community_cards = []
        current_street = "preflop"
        bet_history = ""

    player = Player("CFR", 100)
    player.hand = hand
    agent = CFRAgent(str(model_path))

    action, raise_to = agent.decide(
        GameState(),
        player,
        ["fold", "call", "raise"],
        {
            "min_raise_to": 20,
            "max_bet": 100,
            "pot": 30,
            "current_bet": 10,
        },
    )

    assert action == "call"
    assert raise_to is None
