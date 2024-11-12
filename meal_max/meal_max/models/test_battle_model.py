import unittest
from unittest.mock import patch
from battle_model import BattleModel

# Define a simple Meal class for testing purposes
class Meal:
    def __init__(self, id, meal, price, cuisine, difficulty):
        self.id = id
        self.meal = meal
        self.price = price
        self.cuisine = cuisine
        self.difficulty = difficulty

class TestBattleModel(unittest.TestCase):

    @patch('battle_model.get_random')
    @patch('battle_model.update_meal_stats')
    def test_battle_two_combatants(self, mock_update_meal_stats, mock_get_random):
        # Set up the BattleModel instance
        battle_model = BattleModel()
        
        # Create two Meal instances
        meal1 = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        meal2 = Meal(id=2, meal='Sushi', price=15.0, cuisine='Japanese', difficulty='HIGH')
        
        # Prepare combatants
        battle_model.prep_combatant(meal1)
        battle_model.prep_combatant(meal2)
        
        # Mock get_random to return 0.05
        mock_get_random.return_value = 0.05
        
        # Call battle
        winner = battle_model.battle()
        
        # Assert the winner is correct based on calculated scores
        self.assertEqual(winner, 'Spaghetti')
        
        # Assert update_meal_stats was called correctly
        mock_update_meal_stats.assert_any_call(1, 'win')
        mock_update_meal_stats.assert_any_call(2, 'loss')
        
        # Assert the loser was removed from combatants
        self.assertEqual(len(battle_model.combatants), 1)
        self.assertEqual(battle_model.combatants[0].meal, 'Spaghetti')

    def test_battle_not_enough_combatants(self):
        battle_model = BattleModel()
        
        # Test with no combatants
        with self.assertRaises(ValueError) as context:
            battle_model.battle()
        self.assertEqual(str(context.exception), 'Two combatants must be prepped for a battle.')
        
        # Test with one combatant
        meal1 = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        battle_model.prep_combatant(meal1)
        with self.assertRaises(ValueError) as context:
            battle_model.battle()
        self.assertEqual(str(context.exception), 'Two combatants must be prepped for a battle.')

    def test_prep_combatant_too_many(self):
        battle_model = BattleModel()
        meal1 = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        meal2 = Meal(id=2, meal='Sushi', price=15.0, cuisine='Japanese', difficulty='HIGH')
        meal3 = Meal(id=3, meal='Tacos', price=8.0, cuisine='Mexican', difficulty='LOW')
        
        # Prepare two combatants
        battle_model.prep_combatant(meal1)
        battle_model.prep_combatant(meal2)
        
        # Attempt to add a third combatant
        with self.assertRaises(ValueError) as context:
            battle_model.prep_combatant(meal3)
        self.assertEqual(str(context.exception), 'Combatant list is full, cannot add more combatants.')

    def test_clear_combatants(self):
        battle_model = BattleModel()
        meal1 = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        meal2 = Meal(id=2, meal='Sushi', price=15.0, cuisine='Japanese', difficulty='HIGH')
        
        # Prepare combatants
        battle_model.prep_combatant(meal1)
        battle_model.prep_combatant(meal2)
        
        # Clear combatants and verify
        battle_model.clear_combatants()
        self.assertEqual(len(battle_model.get_combatants()), 0)

    def test_get_battle_score(self):
        battle_model = BattleModel()
        meal = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        
        # Calculate and assert battle score
        score = battle_model.get_battle_score(meal)
        self.assertEqual(score, 68)

    def test_get_combatants(self):
        battle_model = BattleModel()
        meal = Meal(id=1, meal='Spaghetti', price=10.0, cuisine='Italian', difficulty='MED')
        
        # Prepare combatant and verify
        battle_model.prep_combatant(meal)
        combatants = battle_model.get_combatants()
        self.assertEqual(len(combatants), 1)
        self.assertEqual(combatants[0].meal, 'Spaghetti')

if __name__ == '__main__':
    unittest.main()
