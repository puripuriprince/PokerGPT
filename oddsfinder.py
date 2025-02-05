import numpy as np
from numba import njit, prange
from pokerkit import HandUtilities
from collections import Counter
import random

COMBINATIONS_7C5 = np.array([
    [0,1,2,3,4], [0,1,2,3,5], [0,1,2,3,6],
    [0,1,2,4,5], [0,1,2,4,6], [0,1,2,5,6],
    [0,1,3,4,5], [0,1,3,4,6], [0,1,3,5,6],
    [0,1,4,5,6], [0,2,3,4,5], [0,2,3,4,6],
    [0,2,3,5,6], [0,2,4,5,6], [0,3,4,5,6],
    [1,2,3,4,5], [1,2,3,4,6], [1,2,3,5,6],
    [1,2,4,5,6], [1,3,4,5,6], [2,3,4,5,6]
], dtype=np.uint8)

@njit
def evaluate_5card(five_cards):
    ranks = (five_cards // 4).astype(np.int32)
    suits = (five_cards % 4).astype(np.int32)
    rank_counts = np.zeros(13, dtype=np.int32)
    suit_counts = np.zeros(4, dtype=np.int32)
    for i in range(5):
        rank_counts[ranks[i]] += 1
        suit_counts[suits[i]] += 1
    flush = np.any(suit_counts >= 5)
    if flush:
        suit = np.argmax(suit_counts)
        flush_ranks = ranks[suits == suit]
        if len(flush_ranks) < 5:
            flush = False
    unique_ranks = np.unique(ranks)
    straight = False
    if len(unique_ranks) >= 5:
        sorted_ranks = np.sort(unique_ranks)
        for i in range(len(sorted_ranks)-4):
            if sorted_ranks[i+4] - sorted_ranks[i] == 4:
                straight = True
                high = sorted_ranks[i+4]
        if not straight and np.all(sorted_ranks[-4:] == [0, 9, 10, 11, 12]):
            straight = True
            high = 3
    if straight and flush:
        return (8, high)
    if np.any(rank_counts == 4):
        quad_rank = np.argmax(rank_counts)
        kicker = np.max(ranks[ranks != quad_rank])
        return (7, quad_rank, kicker)
    if np.any(rank_counts == 3) and np.any(rank_counts == 2):
        trips_rank = np.argmax(rank_counts == 3)
        pair_rank = np.argmax(rank_counts == 2)
        return (6, trips_rank, pair_rank)
    if flush:
        sorted_flush = np.sort(flush_ranks)[::-1][:5]
        return (5, sorted_flush[0], sorted_flush[1], sorted_flush[2], sorted_flush[3], sorted_flush[4])
    if straight:
        return (4, high)
    if np.any(rank_counts == 3):
        trips_rank = np.argmax(rank_counts)
        kickers = np.sort(ranks[ranks != trips_rank])[::-1][:2]
        return (3, trips_rank, kickers[0], kickers[1])
    if np.sum(rank_counts == 2) >= 2:
        pairs = np.where(rank_counts == 2)[0][::-1]
        kicker = np.max(ranks[~np.isin(ranks, pairs[:2])])
        return (2, pairs[0], pairs[1], kicker)
    if np.any(rank_counts == 2):
        pair_rank = np.argmax(rank_counts)
        kickers = np.sort(ranks[ranks != pair_rank])[::-1][:3]
        return (1, pair_rank, kickers[0], kickers[1], kickers[2])
    high_cards = np.sort(ranks)[::-1][:5]
    return (0, high_cards[0], high_cards[1], high_cards[2], high_cards[3], high_cards[4])

@njit
def evaluate_7hand(seven_cards):
    max_strength = (0,)
    for i in range(21):
        five_card = seven_cards[COMBINATIONS_7C5[i]]
        strength = evaluate_5card(five_card)
        if strength > max_strength:
            max_strength = strength
    return max_strength

@njit(parallel=True)
def monte_carlo_sim(player_hand, community, num_sims):
    deck = np.array([c for c in range(52) if c not in player_hand and c not in community], dtype=np.int32)
    n_comm_needed = 5 - len(community)
    wins = 0
    for i in prange(num_sims):
        np.random.shuffle(deck)
        comm_add = deck[:n_comm_needed]
        opp_hand = deck[n_comm_needed:n_comm_needed+2]
        full_comm = np.concatenate((community, comm_add))
        player_full = np.concatenate((player_hand, full_comm))
        opp_full = np.concatenate((opp_hand, full_comm))
        player_strength = evaluate_7hand(player_full)
        opp_strength = evaluate_7hand(opp_full)
        if player_strength > opp_strength:
            wins += 1
        elif player_strength == opp_strength:
            wins += 0.5
    return wins / num_sims

def calculate_win_percentage(player_hand, community_cards=None, simulations=100000, num_decks=1, num_opponents=1):
    community = list(community_cards) if community_cards else []
    needed_community = 5 - len(community)
    known_cards = Counter(player_hand + community)
    if len(player_hand) != 2:
        raise ValueError("player must have exactly 2 cards")
    if len(community) > 5:
        raise ValueError("too many community cards")
    if any(v > num_decks for v in known_cards.values()):
        raise ValueError("duplicate cards exceed deck count")
    deck = [
        f"{r}{s}"
        for _ in range(num_decks)
        for r in '23456789TJQKA'
        for s in 'shdc'
    ]
    wins = 0
    ties = 0
    for _ in range(simulations):
        temp_deck = list(deck)
        for card in known_cards:
            for _ in range(known_cards[card]):
                if card in temp_deck:
                    temp_deck.remove(card)
        needed = 2*num_opponents + needed_community
        if len(temp_deck) < needed:
            raise ValueError(f"need {needed} cards but only {len(temp_deck)} available")
        random.shuffle(temp_deck)
        new_community = temp_deck[:needed_community]
        temp_deck = temp_deck[needed_community:]
        all_community = community + new_community
        if len(all_community) != 5:
            raise RuntimeError("incorrect  card count")
        player_cards = player_hand + all_community
        player_rank = HandUtilities.get_rank(''.join(player_cards))
        opponent_ranks = []
        for _ in range(num_opponents):
            opp_cards = temp_deck[:2] + all_community
            temp_deck = temp_deck[2:]
            opponent_ranks.append(HandUtilities.get_rank(''.join(opp_cards)))
        results = [
            HandUtilities.compare_ranks(player_rank, opp_rank)
            for opp_rank in opponent_ranks
        ]
        wins += sum(r == 1 for r in results)
        ties += sum(r == 0 for r in results)
    total = simulations * num_opponents
    return (wins/total*100, ties/total*100)

def card_to_index(card_str):
    rank_order = '23456789TJQKA'
    suit_order = {'s':0, 'h':1, 'd':2, 'c':3}
    return rank_order.index(card_str[0].upper()) * 4 + suit_order[card_str[1].lower()]

def index_to_card(index):
    ranks = '23456789TJQKA'
    suits = 'shdc'
    return f"{ranks[index//4]}{suits[index%4]}"

def calculate_odds(player_hand, community_cards=None, simulations=100000, num_decks=1, num_opponents=1, use_pokerkit=True):
    if use_pokerkit:
        return calculate_win_percentage(
            player_hand,
            community_cards,
            simulations,
            num_decks,
            num_opponents
        )
    else:
        ph = np.array([card_to_index(c) for c in player_hand], dtype=np.int32)
        comm = np.array([], dtype=np.int32)
        if community_cards:
            comm = np.array([card_to_index(c) for c in community_cards], dtype=np.int32)
        win_prob = monte_carlo_sim(ph, comm, simulations)
        return win_prob * 100, 0.0

if __name__ == "__main__":
    win, tie = calculate_odds(
        ['As', 'Ac'],
        ['Qh', 'Jh', 'Th'],
        simulations=10000,
        num_opponents=3,
        use_pokerkit=True
    )
    print(f"Win: {win:.1f}% | Tie: {tie:.1f}%")
