import random
from game_functions import GameState, NumberCard, ModifierCard, CardType

# Simulation runner for Flip7 GameState

def run_simulation(target_score=100, bias_hit=0.9):
    """
    Run a full game simulation until one player reaches target_score.

    Args:
        target_score (int): Score threshold to end the game.
        bias_hit (float): Probability of choosing 'Hit' over 'Stay' when both are available.
    """
    gs = GameState()
    history = []
    round_number = 1

    while max(gs.cumulative) < target_score:
        # Start a new round
        gs.round_active = True
        gs.deck = gs.deck.__class__()  # reset deck by creating a new instance
        for p in gs.players:
            p.reset_round()

        round_hist = {
            'actions': [],
            'hits': [0, 0],
            'cards': [[], []],
            'score': [0, 0]
        }

        # Play the round
        while gs.round_active:
            current = gs.current
            actions = gs.get_actions()
            if not actions:
                gs.current ^= 1
                continue
            # bias towards Hit
            if 'Hit' in actions and 'Stay' in actions:
                weights = [bias_hit if a == 'Hit' else 1 - bias_hit for a in actions]
                action = random.choices(actions, weights)[0]
            else:
                action = random.choice(actions)

            round_hist['actions'].append(f"P{current+1}:{action}")
            if action == 'Hit':
                round_hist['hits'][current] += 1

            card = gs.step(action)
            if action == 'Hit' and card is not None:
                round_hist['cards'][current].append(card)

        # End of round: compute scores and update cumulative
        for i, p in enumerate(gs.players):
            pts = gs.compute_round_score(p)
            round_hist['score'][i] = pts
            

        # Print round summary
        print(f"Round {round_number} Summary:")
        print(f"  Actions: {round_hist['actions']}")
        for i in range(2):
            print(f"  Player {i+1}: Hits={round_hist['hits'][i]}, Cards={round_hist['cards'][i]}, Points={round_hist['score'][i]}")
        print(f"  Cumulative Scores: {gs.cumulative}\n")

        history.append(round_hist)
        round_number += 1

    # Final result
    winner = 1 if gs.cumulative[0] < gs.cumulative[1] else 0
    print(f"Game over! Final Scores: Player1={gs.cumulative[0]}, Player2={gs.cumulative[1]}")
    print(f"Winner: Player {winner+1}")
    return history

if __name__ == '__main__':
    # Run simulation with default parameters
    run_simulation()
