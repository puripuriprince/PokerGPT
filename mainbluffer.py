class GtoAnalyzer:
    def __init__(self):
        self.client = OpenAI()

    def evaluate_action(self, stage, pot_odds, equity, actual_action):
        Evaluate how close an action is to GTO play
        Returns a score from 0-1 where 1 is perfect play
        # Calculate optimal action based on pot odds and equity
        optimal_fold_threshold = pot_odds * 100  # Convert to percentage
        if equity < optimal_fold_threshold:
            optimal_action = "fold"
        elif equity > optimal_fold_threshold * 1.5:  # Significant edge
            optimal_action = "raise"
        else:
            optimal_action = "call"
        # Score the actual action
        if actual_action == optimal_action:
            return 1.0
        elif (optimal_action == "raise" and actual_action == "call") or \
             (optimal_action == "call" and actual_action == "fold"):
            return 0.5
        else:
            return 0.0
class PokerBluffer:
    def __init__(self, num_decks=1):
        self.client = OpenAI()
        self.opponents = {}
        self.num_decks = num_decks
        self.gto_analyzer = GtoAnalyzer()  # Add GTO analyzer

    def analyze_opponent_play_quality(self, opponent_name, stage, pot_odds, equity, action):
        """Analyze how close to perfect play an opponent's action was"""
        play_quality = self.gto_analyzer.evaluate_action(stage, pot_odds, equity, action)
        # Update opponent profile with play quality
        if opponent_name in self.opponents:
            opponent = self.opponents[opponent_name]
            prompt = f"""
            Player {opponent_name} made a {action} decision with:
            - Equity: {equity}%
            - Pot odds: {pot_odds}
            - Play quality score: {play_quality}
            Analyze their play style based on this action.
            """
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis = response.choices[0].message.content
                # Update player profile based on analysis
                if play_quality > 0.8:
                    opponent.playing_style = "optimal"
                elif play_quality < 0.3:
                    opponent.playing_style = "erratic"
                
                return analysis
            except Exception as e:
                print(f"Error analyzing play quality: {e}")
                return None
    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        """
        Analyze opponent's playing style using OpenAI API
        Returns updated playing style and aggression level
        """
        prompt = f"""
        Analyze these poker actions for player {opponent_name}:
        {recent_actions}
        
        Determine:
        1. Playing style (tight, loose, aggressive, passive)
        2. Aggression level (1-10)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = response.choices[0].message.content
            
            # Update player profile based on analysis
            # This is a simplified version - you'd want more sophisticated parsing
            if "aggressive" in analysis.lower():
                self.opponents[opponent_name].playing_style = "aggressive"
                self.opponents[opponent_name].aggression_level = min(self.opponents[opponent_name].aggression_level + 1, 10)
            elif "passive" in analysis.lower():
                self.opponents[opponent_name].playing_style = "passive"
                self.opponents[opponent_name].aggression_level = max(self.opponents[opponent_name].aggression_level - 1, 1)
                
            return analysis
        except Exception as e:
            print(f"Error analyzing opponent: {e}")
            return None

    def decide_action(self, pocket_cards, pot_size, opponent_name, stage="preflop", community_cards=None):
        """
        Decide whether to bluff based on:
        1. Real odds of winning
        2. Opponent's playing style
        3. Current game stage
        """
        # Calculate real odds based on game stage
        if stage == "preflop":
            win_percentage, tie_percentage = calculate_preflop_odds(pocket_cards, num_decks=self.num_decks)
        elif stage == "flop":
            win_percentage, tie_percentage = calculate_flop_odds(pocket_cards, community_cards, num_decks=self.num_decks)
        elif stage == "turn":
            win_percentage, tie_percentage = calculate_turn_odds(pocket_cards, community_cards, num_decks=self.num_decks)
        elif stage == "river":
            win_percentage, tie_percentage = calculate_river_odds(pocket_cards, community_cards, num_decks=self.num_decks)
        total_equity = win_percentage + (tie_percentage / 2)
        
        opponent = self.opponents.get(opponent_name)
        if not opponent:
            return "fold"  # Default to safe action if opponent unknown
            
        # Prepare context for AI decision
        prompt = f"""
        As a poker player, decide on an action given:
        - Hand equity: {total_equity}%
        - Opponent style: {opponent.playing_style}
        - Opponent aggression: {opponent.aggression_level}/10
        - Game stage: {stage}
        - Pot size: {pot_size}
        
        Choose and explain one action: call, raise, fold
        Consider if this is a good spot to bluff.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            decision = response.choices[0].message.content.lower()
            
            # Parse the AI's explanation to get the final action
            if "raise" in decision:
                return "raise"
            elif "call" in decision:
                return "call"
            else:
                return "fold"
                
        except Exception as e:
            print(f"Error in decision making: {e}")
            # If API fails, fall back to basic strategy based on equity
            # Pass number of decks to win percentage calculation
            win_percentage, tie_percentage = calculate_win_percentage(pocket_cards, num_decks=self.num_decks)
            total_equity = win_percentage + (tie_percentage / 2)
            
            if total_equity > 70:
                return "raise"
            elif total_equity > 40:
                return "call"
            return "fold"

# Example usage
if __name__ == "__main__":
    bluffer = PokerBluffer()
    
    # Add some opponents
    bluffer.add_opponent("Bob", "tight", 7)
    bluffer.add_opponent("Alice", "loose", 4)
    
    # Example hand
    pocket_cards = ['As', 'Ah']  # Pocket aces
    
    # Update opponent profile based on their recent actions
    recent_actions = """
    Last 3 hands:
    - Raised pre-flop, bet on flop, folded to raise on turn
    - Called pre-flop, checked flop, folded to bet
    - Folded pre-flop
    """
    analysis = bluffer.analyze_opponent_history("Bob", recent_actions)
    print(f"Opponent Analysis: {analysis}")
    
    # Get action decision
    action = bluffer.decide_action(pocket_cards, pot_size=100, opponent_name="Bob")
    print(f"Recommended action: {action}")
