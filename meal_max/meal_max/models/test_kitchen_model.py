import unittest
from unittest.mock import patch, MagicMock, mock_open
from kitchen_model import Meal, create_meal, clear_meals, delete_meal, get_leaderboard, get_meal_by_id, get_meal_by_name, update_meal_stats

class TestKitchenModel(unittest.TestCase):

    def test_meal_init_valid(self):
        meal = Meal(id=1, meal='Spaghetti', cuisine='Italian', price=10.0, difficulty='MED')
        self.assertEqual(meal.meal, 'Spaghetti')
        self.assertEqual(meal.price, 10.0)
        self.assertEqual(meal.difficulty, 'MED')

    def test_meal_init_invalid_price(self):
        with self.assertRaises(ValueError) as context:
            Meal(id=1, meal='Spaghetti', cuisine='Italian', price=-5.0, difficulty='MED')
        self.assertEqual(str(context.exception), 'Price must be a positive value.')

    def test_meal_init_invalid_difficulty(self):
        with self.assertRaises(ValueError) as context:
            Meal(id=1, meal='Spaghetti', cuisine='Italian', price=10.0, difficulty='EXTREME')
        self.assertEqual(str(context.exception), "Difficulty must be 'LOW', 'MED', or 'HIGH'.")

    @patch('kitchen_model.get_db_connection')
    def test_create_meal_valid(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        create_meal('Spaghetti', 'Italian', 10.0, 'MED')

        mock_cursor.execute.assert_called_with("""
                    INSERT INTO meals (meal, cuisine, price, difficulty)
                    VALUES (?, ?, ?, ?)
                """, ('Spaghetti', 'Italian', 10.0, 'MED'))
        mock_conn.commit.assert_called_once()

    @patch('kitchen_model.get_db_connection')
    def test_create_meal_invalid_price(self, mock_get_db_connection):
        with self.assertRaises(ValueError) as context:
            create_meal('Spaghetti', 'Italian', -10.0, 'MED')
        self.assertIn('Invalid price', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_create_meal_invalid_difficulty(self, mock_get_db_connection):
        with self.assertRaises(ValueError) as context:
            create_meal('Spaghetti', 'Italian', 10.0, 'EXTREME')
        self.assertIn('Invalid difficulty level', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_create_meal_duplicate_meal(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [sqlite3.IntegrityError()]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            create_meal('Spaghetti', 'Italian', 10.0, 'MED')
        self.assertIn("Meal with name 'Spaghetti' already exists", str(context.exception))

    @patch('kitchen_model.get_db_connection')
    @patch('builtins.open', new_callable=mock_open, read_data='SQL SCRIPT')
    @patch('os.getenv')
    def test_clear_meals(self, mock_getenv, mock_file, mock_get_db_connection):
        mock_getenv.return_value = '/path/to/sql_script.sql'
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        clear_meals()

        mock_file.assert_called_with('/path/to/sql_script.sql', 'r')
        mock_cursor.executescript.assert_called_with('SQL SCRIPT')
        mock_conn.commit.assert_called_once()

    @patch('kitchen_model.get_db_connection')
    def test_delete_meal_valid(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal exists and not deleted
        mock_cursor.execute.side_effect = [
            None,  # SELECT deleted FROM meals WHERE id = ?
            None   # UPDATE meals SET deleted = TRUE WHERE id = ?
        ]
        mock_cursor.fetchone.return_value = [False]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        delete_meal(1)

        mock_cursor.execute.assert_any_call("SELECT deleted FROM meals WHERE id = ?", (1,))
        mock_cursor.execute.assert_any_call("UPDATE meals SET deleted = TRUE WHERE id = ?", (1,))
        mock_conn.commit.assert_called_once()

    @patch('kitchen_model.get_db_connection')
    def test_delete_meal_already_deleted(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal exists and already deleted
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = [True]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            delete_meal(1)
        self.assertIn('Meal with ID 1 has been deleted', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_delete_meal_not_found(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal not found
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            delete_meal(1)
        self.assertIn('Meal with ID 1 not found', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_get_leaderboard_valid(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate leaderboard data
        mock_cursor.fetchall.return_value = [
            (1, 'Spaghetti', 'Italian', 10.0, 'MED', 5, 3, 0.6),
            (2, 'Sushi', 'Japanese', 15.0, 'HIGH', 10, 7, 0.7)
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        leaderboard = get_leaderboard('wins')
        expected = [
            {
                'id': 1,
                'meal': 'Spaghetti',
                'cuisine': 'Italian',
                'price': 10.0,
                'difficulty': 'MED',
                'battles': 5,
                'wins': 3,
                'win_pct': 60.0
            },
            {
                'id': 2,
                'meal': 'Sushi',
                'cuisine': 'Japanese',
                'price': 15.0,
                'difficulty': 'HIGH',
                'battles': 10,
                'wins': 7,
                'win_pct': 70.0
            }
        ]
        self.assertEqual(leaderboard, expected)

    @patch('kitchen_model.get_db_connection')
    def test_get_leaderboard_invalid_sort_by(self, mock_get_db_connection):
        with self.assertRaises(ValueError) as context:
            get_leaderboard('invalid_sort')
        self.assertIn('Invalid sort_by parameter', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_id_valid(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal found and not deleted
        mock_cursor.fetchone.return_value = (1, 'Spaghetti', 'Italian', 10.0, 'MED', False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        meal = get_meal_by_id(1)
        self.assertEqual(meal.meal, 'Spaghetti')
        self.assertEqual(meal.price, 10.0)

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_id_deleted(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal found and deleted
        mock_cursor.fetchone.return_value = (1, 'Spaghetti', 'Italian', 10.0, 'MED', True)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            get_meal_by_id(1)
        self.assertIn('Meal with ID 1 has been deleted', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_id_not_found(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal not found
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            get_meal_by_id(1)
        self.assertIn('Meal with ID 1 not found', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_name_valid(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal found and not deleted
        mock_cursor.fetchone.return_value = (1, 'Spaghetti', 'Italian', 10.0, 'MED', False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        meal = get_meal_by_name('Spaghetti')
        self.assertEqual(meal.meal, 'Spaghetti')
        self.assertEqual(meal.price, 10.0)

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_name_deleted(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal found and deleted
        mock_cursor.fetchone.return_value = (1, 'Spaghetti', 'Italian', 10.0, 'MED', True)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            get_meal_by_name('Spaghetti')
        self.assertIn('Meal with name Spaghetti has been deleted', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_get_meal_by_name_not_found(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal not found
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            get_meal_by_name('Spaghetti')
        self.assertIn('Meal with name Spaghetti not found', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_update_meal_stats_win(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal exists and not deleted
        mock_cursor.fetchone.return_value = [False]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        update_meal_stats(1, 'win')

        mock_cursor.execute.assert_any_call("SELECT deleted FROM meals WHERE id = ?", (1,))
        mock_cursor.execute.assert_any_call("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?", (1,))
        mock_conn.commit.assert_called_once()

    @patch('kitchen_model.get_db_connection')
    def test_update_meal_stats_loss(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal exists and not deleted
        mock_cursor.fetchone.return_value = [False]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        update_meal_stats(1, 'loss')

        mock_cursor.execute.assert_any_call("SELECT deleted FROM meals WHERE id = ?", (1,))
        mock_cursor.execute.assert_any_call("UPDATE meals SET battles = battles + 1 WHERE id = ?", (1,))
        mock_conn.commit.assert_called_once()

    @patch('kitchen_model.get_db_connection')
    def test_update_meal_stats_invalid_result(self, mock_get_db_connection):
        with self.assertRaises(ValueError) as context:
            update_meal_stats(1, 'draw')
        self.assertIn("Invalid result: draw. Expected 'win' or 'loss'.", str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_update_meal_stats_deleted_meal(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal deleted
        mock_cursor.fetchone.return_value = [True]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            update_meal_stats(1, 'win')
        self.assertIn('Meal with ID 1 has been deleted', str(context.exception))

    @patch('kitchen_model.get_db_connection')
    def test_update_meal_stats_not_found(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simulate meal not found
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        with self.assertRaises(ValueError) as context:
            update_meal_stats(1, 'win')
        self.assertIn('Meal with ID 1 not found', str(context.exception))

if __name__ == '__main__':
    unittest.main()
