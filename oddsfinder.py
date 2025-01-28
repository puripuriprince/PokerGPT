
import random
from treys import Card, Deck, Evaluator

def calculate_win_percentage(pocket_pair, simulations=100000, num_decks=1):
    """
    Simulate poker hands to calculate the win percentage for a given pocket pair.
    
    :param pocket_pair: The pocket pair (as a list of card strings, e.g., ['As', 'Ah']).
    :param simulations: Number of hands to simulate (default: 100,000).
    :return: Win percentage for the pocket pair against a random hand.
    """
    evaluator = Evaluator()
    win_count = 0
    tie_count = 0
    total_count = 0
    
    for _ in range(simulations):
        # Create deck(s) and shuffle
        if num_decks == 1:
            deck = Deck()
        else:
            # For multiple decks, create a combined deck
            deck = Deck()
            for _ in range(num_decks - 1):
                additional_deck = Deck()
                deck.cards.extend(additional_deck.cards)
            random.shuffle(deck.cards)
        
        # Remove the pocket pair from the deck (the player's hand)
        hand = [Card.new(card) for card in pocket_pair]
        deck.cards.remove(hand[0])
        deck.cards.remove(hand[1])
        
        # Deal a random hand to the opponent
        opponent_hand = [deck.draw(1)[0], deck.draw(1)[0]]
        
        # Deal the community cards (flop, turn, and river)
        community_cards = [deck.draw(1)[0] for _ in range(5)]
        
        # Evaluate both hands
        player_score = evaluator.evaluate(hand, community_cards)
        opponent_score = evaluator.evaluate(opponent_hand, community_cards)
        
        # Compare the scores
        if player_score < opponent_score:
            win_count += 1
        elif player_score == opponent_score:
            tie_count += 1
        total_count += 1
    
    win_percentage = (win_count / total_count) * 100
    tie_percentage = (tie_count / total_count) * 100
    
    return win_percentage, tie_percentage

# Example usage
pocket_pair = ['As', 'Ac']  # Pocket Aces
win_percentage, tie_percentage = calculate_win_percentage(pocket_pair)

print(f"Win Percentage: {win_percentage}%")
print(f"Tie Percentage: {tie_percentage}%")




def calculate_win_percentage(pocket_pair, community_cards=None, simulations=100000, num_decks=1):




        # Use provided community cards or deal new ones
        if community_cards:
            # Convert provided cards to Card objects if they're strings
            board = [Card.new(card) if isinstance(card, str) else card for card in community_cards]
            # Deal remaining community cards if needed
            remaining = 5 - len(board)
            board.extend([deck.draw(1)[0] for _ in range(remaining)])
        else:
            board = [deck.draw(1)[0] for _ in range(5)]