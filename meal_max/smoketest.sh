#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5001/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# Function to URL-encode strings
urlencode() {
    local length="${#1}"
    local encoded=""
    for (( i = 0; i < length; i++ )); do
        local c="${1:i:1}"
        case "$c" in
            [a-zA-Z0-9.~_-]) encoded+="$c" ;;
            *) encoded+=$(printf '%%%02X' "'$c") ;;
        esac
    done
    echo "$encoded"
}

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  response=$(curl -s -X GET "$BASE_URL/health")
  if echo "$response" | grep -q '"status": "healthy"'; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  response=$(curl -s -X GET "$BASE_URL/db-check")
  if echo "$response" | grep -q '"database_status": "healthy"'; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal & Leaderboard Management
#
##########################################################

clear_meals() {
    echo "Clearing all meals..."
    response=$(curl -s -X DELETE "$BASE_URL/clear-meals")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "All meals cleared successfully."
    else
        echo "Failed to clear meals."
        exit 1
    fi
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal) to the database..."

  json_payload=$(jq -n \
    --arg meal "$meal" \
    --arg cuisine "$cuisine" \
    --arg price "$price" \
    --arg difficulty "$difficulty" \
    '{meal: $meal, cuisine: $cuisine, price: ($price|tonumber), difficulty: $difficulty}')

  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "$json_payload")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_leaderboard() {
    echo "Getting all meals in the leaderboard..."
    response=$(curl -s -X GET "$BASE_URL/get-all-meals-from-leaderboard")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Leaderboard retrieved successfully."
        if [ "$ECHO_JSON" = true ]; then
            echo "Meals JSON:"
            echo "$response" | jq .
        fi
    else
        echo "Failed to get Leaderboard."
        exit 1
    fi
}

get_meal_by_id() {
    meal_id=$1

    echo "Getting meal by ID ($meal_id)..."
    response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-id/$meal_id")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Meal retrieved successfully by ID ($meal_id)."
        if [ "$ECHO_JSON" = true ]; then
            echo "Meal JSON (ID $meal_id):"
            echo "$response" | jq .
        fi
    else
        echo "Failed to get meal by ID ($meal_id)."
        exit 1
    fi
}

get_meal_by_name() {
    meal_name=$1
    encoded_meal_name=$(urlencode "$meal_name")

    echo "Getting meal by name ($meal_name)..."
    response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-name/$encoded_meal_name")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Meal retrieved successfully by name ($meal_name)."
        if [ "$ECHO_JSON" = true ]; then
            echo "Meal JSON (Name $meal_name):"
            echo "$response" | jq .
        fi
    else
        echo "Failed to get meal by name ($meal_name)."
        exit 1
    fi
}

##########################################################
#
# Battle Management
#
##########################################################

# Function to clear combatants
clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X DELETE "$BASE_URL/clear-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
      echo "Combatants cleared successfully."
  else
      echo "Failed to clear combatants."
      exit 1
  fi
}

# Function to prepare a combatant
prep_combatant() {
  meal_id=$1

  echo "Preparing combatant with Meal ID ($meal_id)..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant prepared successfully."
  else
    echo "Failed to prepare combatant."
    exit 1
  fi
}

# Function to get current combatants
get_combatants() {
  echo "Getting current combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get combatants."
    exit 1
  fi
}

# Function to start a battle
start_battle() {
  echo "Starting battle..."
  response=$(curl -s -X POST "$BASE_URL/start-battle")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Result JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to start battle."
    exit 1
  fi
}

##########################################################
#
# Run Smoke Tests
#
##########################################################

# Health checks
check_health
check_db

# Clear meals and combatants
clear_meals
clear_combatants

# Create meals
create_meal "Spaghetti" "Italian" 15.99 "MED"        # Meal ID 1
create_meal "Wagyu Steak" "Japanese" 57.99 "HIGH"    # Meal ID 2
create_meal "Mc Nuggets" "American" 0.01 "LOW"       # Meal ID 3
create_meal "Jello Salad" "American" 1.00 "MED"      # Meal ID 4
create_meal "Burrito" "Mexican" 10000.00 "MED"       # Meal ID 5

# Delete a meal
delete_meal 1

# Get leaderboard
get_leaderboard

# Get meal by ID and name
get_meal_by_id 2
get_meal_by_name "Jello Salad"
get_meal_by_id 2

# Clear meals again
clear_meals

# Create meals again
create_meal "Burrito" "Mexican" 10000.00 "MED"       # Meal ID 1
create_meal "Wagyu Steak" "Japanese" 57.99 "HIGH"    # Meal ID 2
create_meal "Mc Nuggets" "American" 0.01 "LOW"       # Meal ID 3
create_meal "Jello Salad" "American" 1.00 "MED"      # Meal ID 4
create_meal "Spaghetti" "Italian" 15.99 "MED"        # Meal ID 5

# Prepare combatants
prep_combatant 1  # Burrito
prep_combatant 2  # Wagyu Steak

# Get combatants
get_combatants

# Start battle
start_battle

# Get leaderboard to see updated stats
get_leaderboard

# Prepare next combatant
prep_combatant 3  # Mc Nuggets

# Get combatants
get_combatants

# Start another battle
start_battle

# Get final leaderboard
get_leaderboard

echo "All tests passed successfully!"
