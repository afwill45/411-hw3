# test_kitchen_model.py

import pytest
import sqlite3
from contextlib import contextmanager
from meal_max.models.kitchen_model import (
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

# #################################################
# # Fixtures and Mocks
# #################################################

@pytest.fixture
def mock_db_connection(mocker):
    """Fixture to mock the database connection."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None  # Simulate commit behavior

    # Patch `get_db_connection` where it is imported in `kitchen_model`
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection instead of the cursor

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_conn  # Return mock_conn for assertions in tests

# #################################################
# # Test Cases
# #################################################

def test_create_meal(mock_db_connection):
    """Test creating a new meal."""
    create_meal("Pasta", cuisine="Italian", price=12.5, difficulty="MED")
    assert mock_db_connection.cursor().execute.called, "Expected SQL execute to be called."
    assert mock_db_connection.commit.called, "Expected connection commit to be called."

def test_create_meal_duplicate(mock_db_connection):
    """Test creating a meal that already exists."""
    mock_db_connection.cursor().execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meal.name")
    
    with pytest.raises(ValueError, match="Meal with name 'Pasta' already exists"):
        create_meal("Pasta", cuisine="Italian", price=12.5, difficulty="MED")

def test_clear_meals(mock_db_connection, mocker):
    """Test clearing all meals from the database."""
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': '/app/sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="CREATE TABLE meals ..."))
    
    clear_meals()
    mock_open.assert_called_once_with('/app/sql/create_meal_table.sql', 'r')
    assert mock_db_connection.cursor().executescript.called, "Expected SQL executescript to be called."
    assert mock_db_connection.commit.called, "Expected connection commit to be called."

def test_delete_meal(mock_db_connection):
    """Test deleting a meal by ID."""
    mock_db_connection.cursor().fetchone.return_value = (False,)  # Simulate meal not being deleted
    
    delete_meal(1)
    assert mock_db_connection.cursor().execute.called, "Expected SQL execute to be called."
    assert mock_db_connection.commit.called, "Expected connection commit to be called."

def test_delete_meal_already_deleted(mock_db_connection):
    """Test deleting a meal that has already been marked as deleted."""
    mock_db_connection.cursor().fetchone.return_value = (True,)  # Simulate meal already deleted
    
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)

def test_delete_meal_not_found(mock_db_connection):
    """Test deleting a meal that does not exist."""
    mock_db_connection.cursor().fetchone.return_value = None  # Simulate meal not found

    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        delete_meal(1)

def test_get_meal_by_name(mock_db_connection):
    """Test retrieving a meal by name."""
    # Mock the expected tuple structure as per the actual function's requirements
    mock_db_connection.cursor().fetchone.return_value = (1, "Pasta", "Italian", 12.5, "MED", False)
    
    meal = get_meal_by_name("Pasta")
    assert meal.meal == "Pasta", "Expected to retrieve meal with name 'Pasta'"
    assert meal.cuisine == "Italian", "Expected cuisine to be 'Italian'"
    assert meal.price == 12.5, "Expected price to be 12.5"
    assert meal.difficulty == "MED", "Expected difficulty to be 'MED'"

def test_get_meal_by_name_not_found(mock_db_connection):
    """Test retrieving a meal that does not exist."""
    mock_db_connection.cursor().fetchone.return_value = None  # Simulate meal not found

    with pytest.raises(ValueError, match="Meal with name Pasta not found"):
        get_meal_by_name("Pasta")

def test_get_leaderboard_empty(mock_db_connection):
    """Test retrieving leaderboard when there are no meals."""
    mock_db_connection.cursor().fetchall.return_value = []  # Simulate empty leaderboard

    leaderboard = get_leaderboard()
    assert leaderboard == [], "Expected an empty leaderboard"

def test_get_leaderboard_with_meals(mock_db_connection):
    """Test retrieving leaderboard with meals."""
    # Mock the expected structure for the leaderboard
    mock_db_connection.cursor().fetchall.return_value = [
        (1, "Pasta", "Italian", 12.5, "MED", 20, 10, 0.5),
        (2, "Burger", "American", 8.0, "LOW", 15, 8, 0.5333)
    ]

    leaderboard = get_leaderboard()
    expected_leaderboard = [
        {
            'id': 1,
            'meal': "Pasta",
            'cuisine': "Italian",
            'price': 12.5,
            'difficulty': "MED",
            'battles': 20,
            'wins': 10,
            'win_pct': 50.0
        },
        {
            'id': 2,
            'meal': "Burger",
            'cuisine': "American",
            'price': 8.0,
            'difficulty': "LOW",
            'battles': 15,
            'wins': 8,
            'win_pct': 53.3
        }
    ]
    assert leaderboard == expected_leaderboard, "Expected leaderboard to contain specified meals with correct details"

def test_update_meal_stats_win(mock_db_connection):
    """Test updating meal stats with a win."""
    mock_db_connection.cursor().fetchone.return_value = (False,)  # Simulate meal is not deleted
    update_meal_stats(1, 'win')
    mock_db_connection.cursor().execute.assert_called_with(
        "UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?",
        (1,)
    )
    assert mock_db_connection.commit.called, "Expected connection commit to be called"

def test_update_meal_stats_loss(mock_db_connection):
    """Test updating meal stats with a loss."""
    mock_db_connection.cursor().fetchone.return_value = (False,)  # Simulate meal is not deleted
    update_meal_stats(1, 'loss')
    mock_db_connection.cursor().execute.assert_called_with(
        "UPDATE meals SET battles = battles + 1 WHERE id = ?",
        (1,)
    )
    assert mock_db_connection.commit.called, "Expected connection commit to be called"

def test_update_meal_stats_invalid_result(mock_db_connection):
    """Test updating meal stats with an invalid result."""
    mock_db_connection.cursor().fetchone.return_value = (False,)  # Simulate meal is not deleted
    with pytest.raises(ValueError, match="Invalid result: draw. Expected 'win' or 'loss'."):
        update_meal_stats(1, 'draw')

def test_update_meal_stats_deleted_meal(mock_db_connection):
    """Test updating stats of a deleted meal."""
    mock_db_connection.cursor().fetchone.return_value = (True,)  # Simulate meal is deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, 'win')
