import requests
import json
import numpy as np
from collections import defaultdict, deque

# Configuration
OPENROUTER_API_KEY = "your-api-key"
DEEPSEEK_MODEL = "deepseek\deepseel-r1"
MAX_HISTORY = 10  # Last 10 moves remembered per player

class PokerAIAnalyzer:
    def __init__(self):
        self.player_profiles = defaultdict(lambda: {
            'aggression': 0.5,
            'bluff_tendency': 0.2,
            'call_frequency': 0.6,
            'action_history': deque(maxlen=MAX_HISTORY)
        })
        self.game_history = []
        self.current_pot = 0
        self.blind_structure = (50, 100)
        self.stack_sizes = {}

    def calculate_odds(self, hand, board, num_players=6, simulations=3000):
        # ... (Implement your hand equity calculator here) ...
        # Return win_prob, tie_prob
        return 0.35, 0.05  # Placeholder

    def update_profiles(self, action_sequence):
        for player_id, action in action_sequence.items():
            profile = self.player_profiles[player_id]
            profile['action_history'].append(action)
            
            # Analyze aggression
            aggressive_actions = sum(1 for a in profile['action_history'] 
                                   if a['action'] in ['raise', 'all-in'])
            profile['aggression'] = aggressive_actions / len(profile['action_history'])
            
            # Calculate bluff tendency (simplified)
            if action['action'] == 'bluff':
                profile['bluff_tendency'] = 0.9 * profile['bluff_tendency'] + 0.1
            else:
                profile['bluff_tendency'] *= 0.95

    def build_context_prompt(self, hand, board, win_prob, players):
        prompt = f"""Poker Decision Context:
Current Hand: {hand}
Community Cards: {board}
Win Probability: {win_prob:.1%}
Pot Size: {self.current_pot}
Your Stack: {self.stack_sizes['hero']}
Blinds: {self.blind_structure}
        
Player Profiles:
"""
        for pid, profile in players.items():
            prompt += f"""- Player {pid}:
  Aggression: {profile['aggression']:.0%}
  Bluff Tendency: {profile['bluff_tendency']:.0%}
  Recent Actions: {list(profile['action_history'])[-3:]}
  
"""
        prompt += """\nConsidering the pot odds, table position, and opponent tendencies, recommend the action with confidence percentage. Output format: {"action": "raise", "amount": 500, "confidence": 65}"""
        return prompt

    def ai_decision(self, prompt):
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.7,
            "max_tokens": 150
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                    headers=headers, data=json.dumps(payload))
            response_data = json.loads(response.text)
            return json.loads(response_data['choices'][0]['message']['content'])
        except Exception as e:
            print(f"API Error: {e}")
            return {"action": "check", "confidence": 50}

class GameStateTracker:
    def __init__(self):
        self.current_hand = []
        self.community_cards = []
        self.action_sequence = []
        self.players = {}
        self.analyzers = PokerAIAnalyzer()

    def new_hand(self, hand, players):
        self.current_hand = hand
        self.community_cards = []
        self.players = players
        self.analyzers.stack_sizes = players

    def update_board(self, cards):
        self.community_cards.extend(cards)

    def record_action(self, player_id, action):
        self.action_sequence.append({
            'player': player_id,
            'action': action['type'],
            'amount': action.get('amount', 0),
            'stage': len(self.community_cards)  # Track round
        })
        self.analyzers.update_profiles({player_id: action})

    def get_ai_decision(self):
        win_prob, tie_prob = self.analyzers.calculate_odds(
            self.current_hand, self.community_cards
        )
        prompt = self.analyzers.build_context_prompt(
            self.current_hand, self.community_cards,
            win_prob, self.analyzers.player_profiles
        )
        return self.analyzers.ai_decision(prompt)

# game logic
game = GameStateTracker()

# Start new hand
game.new_hand(
    hand=['As', 'Kh'],
    players={'me': 1500, 'villain1': 1200, 'villain2': 1800}
)

# Record previous actions
game.record_action('villain1', {'type': 'raise', 'amount': 300})
game.record_action('villain2', {'type': 'call'})

# Update board
game.update_board(['Qs', '7h', '2d'])

# Get AI decision
decision = game.get_ai_decision()
print(f"AI recommends: {decision['action']} with {['confidence']}% confidence")
