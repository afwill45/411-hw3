#Just slapping in the first few lines of the playlist version. Not 100% sure what they do yet.
#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

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

###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
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
  echo "Clearing all meals"
  curl -s -X DELETE "$BASE_URL/clear-catalog" | grep -q '"status": "success"'
}

create_meal(){
    meal=$1
    cuisine=$2 
    price=$3
    difficulty=$4
    
    echo "Adding meal ($meal) to the database..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal(){
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
    echo "All meals retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meals JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meals."
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

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-name/$meal_name")
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

#this doesn't work at all yet
update_meal_stats() {
    meal_id=$1
    result=$2

    echo "Updating meal battle statistics..."
    response=$(curl -s -X POST "$BASE_URL/update-meal-stats")
    if [ $? -eq 0 ]; then
        echo "Meal stats updated successfully."
    else
        echo "Failed to update meal stats."
        exit 1
  fi

}





# Health checks
check_health
check_db

# Clear the catalog
clear_meals

# Create meals
create_meal "Spaghetti" "Italian" 15.99 "MED"
create_meal "Wagyu Steak" "Japanese" 57.99 "HIGH"
create_meal "Mc Nuggets" "American" 0.01 "LOW"
create_meal "Jello Salad" "American" 1.00 "MED"
create_meal "Burrito" "Mexican" 10000.00 "MED"

delete_meal 1
get_leaderboard
get_meal_by_id 2
get_meal_by_name "Jello Salad"

clear_meals

create_meal "Burrito" "Mexican" 10000.00 "MED"
create_meal "Wagyu Steak" "Japanese" 57.99 "HIGH"
create_meal "Mc Nuggets" "American" 0.01 "LOW"
create_meal "Jello Salad" "American" 1.00 "MED"
create_meal "Spaghetti" "Italian" 15.99 "MED"

update_meal_stats 1 "win"