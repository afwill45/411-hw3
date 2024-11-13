# test_battle_model.py

import pytest
from unittest.mock import patch
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

# #################################################
# # Test Cases
# #################################################

def test_prep_combatant():
    """Test adding a single combatant."""
    battle_model = BattleModel()
    meal = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    battle_model.prep_combatant(meal)
    assert battle_model.combatants == [meal], "Expected combatants list to contain the added meal."

def test_prep_two_combatants():
    """Test adding two combatants."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    meal2 = Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW")
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    assert battle_model.combatants == [meal1, meal2], "Expected combatants list to contain both meals."

def test_prep_combatant_full():
    """Test adding a combatant when the list is already full."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    meal2 = Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW")
    meal3 = Meal(id=3, meal="Sushi", cuisine="Japanese", price=15.0, difficulty="HIGH")
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(meal3)

def test_get_combatants():
    """Test retrieving the list of combatants."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    battle_model.prep_combatant(meal1)
    combatants = battle_model.get_combatants()
    assert combatants == [meal1], "Expected to retrieve the current list of combatants."

def test_clear_combatants():
    """Test clearing the combatants list."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    battle_model.prep_combatant(meal1)
    battle_model.clear_combatants()
    assert battle_model.combatants == [], "Expected combatants list to be empty after clearing."

def test_get_battle_score():
    """Test calculating the battle score for a combatant."""
    battle_model = BattleModel()
    meal = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    score = battle_model.get_battle_score(meal)
    expected_score = (12.5 * len("Italian")) - 2  # (12.5 * 7) - 2 = 85.5
    assert score == expected_score, f"Expected battle score to be {expected_score}, got {score}."

def test_get_battle_score_invalid_difficulty():
    """Test get_battle_score with an invalid difficulty level."""
    battle_model = BattleModel()
    meal = Meal(id=1, meal="InvalidMeal", cuisine="Cuisine", price=10.0, difficulty="MED")
    # Manually set difficulty to an invalid value to bypass validation
    meal.difficulty = "INVALID"
    with pytest.raises(KeyError):
        battle_model.get_battle_score(meal)

def test_battle_not_enough_combatants():
    """Test starting a battle with less than two combatants."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    battle_model.prep_combatant(meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.get_random', return_value=0.1)
def test_battle_winner_combatant1(mock_get_random, mock_update_meal_stats):
    """Test battle where combatant 1 wins (delta > random number)."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")  # Score: 85.5
    meal2 = Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW")  # Score: 61.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    winner_meal_name = battle_model.battle()
    assert winner_meal_name == "Pasta", "Expected 'Pasta' to win the battle."
    mock_update_meal_stats.assert_any_call(meal1.id, 'win')
    mock_update_meal_stats.assert_any_call(meal2.id, 'loss')
    assert battle_model.combatants == [meal1], "Expected only the winner to remain in combatants."

@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.get_random', return_value=0.3)
def test_battle_winner_combatant2(mock_get_random, mock_update_meal_stats):
    """Test battle where combatant 2 wins (delta <= random number)."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")  # Score: 85.5
    meal2 = Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW")  # Score: 61.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    winner_meal_name = battle_model.battle()
    assert winner_meal_name == "Burger", "Expected 'Burger' to win the battle."
    mock_update_meal_stats.assert_any_call(meal2.id, 'win')
    mock_update_meal_stats.assert_any_call(meal1.id, 'loss')
    assert battle_model.combatants == [meal2], "Expected only the winner to remain in combatants."

@patch('meal_max.models.battle_model.update_meal_stats')
def test_battle_low_scores(mock_update_meal_stats):
    """Test battle where combatants have low scores and minimal delta."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="LowScoreMeal1", cuisine="Short", price=1.0, difficulty="HIGH")  # Score: 4.0
    meal2 = Meal(id=2, meal="LowScoreMeal2", cuisine="Tiny", price=1.0, difficulty="HIGH")  # Score: 3.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    # Set random_number less than delta (delta = 0.01)
    with patch('meal_max.models.battle_model.get_random', return_value=0.005):
        winner_meal_name = battle_model.battle()
    assert winner_meal_name == "LowScoreMeal1", "Expected 'LowScoreMeal1' to win the battle."
    assert battle_model.combatants == [meal1], "Expected only the winner to remain in combatants."


@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.get_random', return_value=0.0)
def test_battle_maximum_delta(mock_get_random, mock_update_meal_stats):
    """Test battle where delta is maximum and combatant 1 should always win."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="ExpensiveMeal", cuisine="LongCuisineName", price=1000.0, difficulty="LOW")  # Very high score
    meal2 = Meal(id=2, meal="CheapMeal", cuisine="Short", price=1.0, difficulty="HIGH")  # Very low score
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    winner_meal_name = battle_model.battle()
    assert winner_meal_name == "ExpensiveMeal", "Expected 'ExpensiveMeal' to win the battle due to maximum delta."
    mock_update_meal_stats.assert_any_call(meal1.id, 'win')
    mock_update_meal_stats.assert_any_call(meal2.id, 'loss')
    assert battle_model.combatants == [meal1], "Expected only the winner to remain in combatants."

@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.get_random', return_value=0.9999)
def test_battle_minimum_delta(mock_get_random, mock_update_meal_stats):
    """Test battle where delta is minimal and combatant 2 should win due to high random number."""
    battle_model = BattleModel()
    # Create meals with very close scores
    meal1 = Meal(id=1, meal="Meal1", cuisine="Cuisine", price=10.0, difficulty="MED")  # Score: 68.0
    meal2 = Meal(id=2, meal="Meal2", cuisine="Cuisine", price=10.1, difficulty="MED")  # Score: 69.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    winner_meal_name = battle_model.battle()
    assert winner_meal_name == "Meal2", "Expected 'Meal2' to win due to minimal delta and high random number."
    mock_update_meal_stats.assert_any_call(meal2.id, 'win')
    mock_update_meal_stats.assert_any_call(meal1.id, 'loss')
    assert battle_model.combatants == [meal2], "Expected only the winner to remain in combatants."

@patch('meal_max.models.battle_model.update_meal_stats')
def test_battle_after_clearing_combatants(mock_update_meal_stats):
    """Test attempting to battle after clearing combatants."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Meal1", cuisine="Cuisine", price=10.0, difficulty="MED")
    meal2 = Meal(id=2, meal="Meal2", cuisine="Cuisine", price=10.0, difficulty="MED")
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    battle_model.clear_combatants()
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

@patch('meal_max.models.battle_model.update_meal_stats')
def test_adding_combatant_after_battle(mock_update_meal_stats):
    """Test adding a new combatant after a battle."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Meal1", cuisine="Cuisine", price=10.0, difficulty="MED")  # Score: 68.0
    meal2 = Meal(id=2, meal="Meal2", cuisine="Cuisine", price=12.0, difficulty="MED")  # Score: 82.0
    meal3 = Meal(id=3, meal="Meal3", cuisine="Cuisine", price=15.0, difficulty="MED")
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    # Adjust get_random to ensure meal2 wins (delta = 0.14, get_random = 0.14)
    with patch('meal_max.models.battle_model.get_random', return_value=0.14):
        winner_name = battle_model.battle()
    # Now add a new combatant
    battle_model.prep_combatant(meal3)
    assert battle_model.combatants == [meal2, meal3], "Expected combatants list to contain meal2 and meal3."

@patch('meal_max.models.battle_model.update_meal_stats')
def test_repeated_battles(mock_update_meal_stats):
    """Test performing multiple battles in succession."""
    battle_model = BattleModel()
    meals = [
        Meal(id=1, meal="Meal1", cuisine="Cuisine1", price=10.0, difficulty="MED"),  # Score: 68.0
        Meal(id=2, meal="Meal2", cuisine="Cuisine2", price=12.0, difficulty="LOW"),  # Score: 92.0
        Meal(id=3, meal="Meal3", cuisine="Cuisine3", price=8.0, difficulty="HIGH")   # Score: 57.0
    ]
    battle_model.prep_combatant(meals[0])
    battle_model.prep_combatant(meals[1])
    # First battle (delta = 0.24, get_random = 0.25)
    with patch('meal_max.models.battle_model.get_random', return_value=0.25):
        winner_name = battle_model.battle()
    assert len(battle_model.combatants) == 1, "Expected one combatant after first battle."
    # Add next combatant
    battle_model.prep_combatant(meals[2])
    # Second battle (delta = 0.35, get_random = 0.35)
    with patch('meal_max.models.battle_model.get_random', return_value=0.35):
        winner_name = battle_model.battle()
    assert len(battle_model.combatants) == 1, "Expected one combatant after second battle."

@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.get_random', return_value=0.35)
def test_update_meal_stats_called_correctly(mock_get_random, mock_update_meal_stats):
    """Test that update_meal_stats is called with correct parameters."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Meal1", cuisine="Cuisine", price=10.0, difficulty="MED")  # Score: 68.0
    meal2 = Meal(id=2, meal="Meal2", cuisine="Cuisine", price=15.0, difficulty="LOW")  # Score: 102.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    battle_model.battle()
    mock_update_meal_stats.assert_any_call(meal2.id, 'win')
    mock_update_meal_stats.assert_any_call(meal1.id, 'loss')

@patch('meal_max.models.battle_model.update_meal_stats')
def test_battle_logging(mock_update_meal_stats, caplog):
    """Test that battle method logs appropriate messages."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="Meal1", cuisine="Cuisine", price=10.0, difficulty="MED")  # Score: 68.0
    meal2 = Meal(id=2, meal="Meal2", cuisine="Cuisine", price=15.0, difficulty="LOW")  # Score: 102.0
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    with patch('meal_max.models.battle_model.get_random', return_value=0.35):
        battle_model.battle()
    # Check if log contains specific messages
    assert "Two meals enter, one meal leaves!" in caplog.text
    assert "Battle started between Meal1 and Meal2" in caplog.text
    assert "The winner is: Meal2" in caplog.text

@patch('meal_max.models.battle_model.update_meal_stats')
def test_battle_with_extreme_values(mock_update_meal_stats):
    """Test battle with meals having extreme attribute values."""
    battle_model = BattleModel()
    meal1 = Meal(id=1, meal="ExpensiveMeal", cuisine="CuisineName", price=10000.0, difficulty="LOW")  # Very high score
    meal2 = Meal(id=2, meal="CheapMeal", cuisine="C", price=0.01, difficulty="HIGH")  # Very low score
    battle_model.prep_combatant(meal1)
    battle_model.prep_combatant(meal2)
    with patch('meal_max.models.battle_model.get_random', return_value=0.5):
        winner_name = battle_model.battle()
    assert winner_name == "ExpensiveMeal", "Expected 'ExpensiveMeal' to win due to extreme high score."
    assert battle_model.combatants == [meal1], "Expected only the winner to remain in combatants."

def test_prep_combatant_invalid_meal():
    """Test adding a combatant with invalid meal data."""
    battle_model = BattleModel()
    with pytest.raises(ValueError, match="Price must be a positive value."):
        Meal(id=1, meal="InvalidMeal", cuisine="Cuisine", price=-5.0, difficulty="MED")  # Invalid price

