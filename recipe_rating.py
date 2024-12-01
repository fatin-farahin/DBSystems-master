# recipe_rating.py

import streamlit as st
import pandas as pd
from db_connection import connect_db

def display_rating(recipe_rating):
    """Display the rating with stars or 'No ratings yet' if no rating exists."""
    if pd.isna(recipe_rating) or recipe_rating == 0:
        return "No ratings yet"
    
    # Ensure the rating is within the 0-5 range
    recipe_rating = max(0, min(recipe_rating, 5))
    
    full_stars = "★" * int(recipe_rating)  # Unicode star for filled stars
    empty_stars = "☆" * (5 - int(recipe_rating))  # Unicode star for empty stars
    return full_stars + empty_stars

def rate_recipe(recipe_id):
    db = connect_db()
    ratings_collection = db["recipe_ratings"]
    recipes_collection = db["recipes"]
    users_collection = db["users"]

    # Ensure recipe_id is stored as an integer
    recipe_id = int(recipe_id)

    # Get logged-in user (if any)
    logged_in_user = st.session_state.get('logged_in')
    st.write(f"Logged-in user: {logged_in_user}")  # Debug: check if the user is logged in

    if logged_in_user:
        user_id = st.session_state.get('user_id')  # Fetch user_id from session state
    else:
        user_id = None  # Handle guest users or assign a special guest ID

    st.write(f"User ID for rating: {user_id}")  # Debug line

    # Get the recipe
    recipe = recipes_collection.find_one({"recipe_id": recipe_id})

    # If recipe is not found, handle the error
    if not recipe:
        st.error("Recipe not found.")
        return
    
    # Check if the user is logged in
    user_id = st.session_state.get("logged_in_user", {}).get("user_id")

    if not user_id:
        st.error("You need to log in to rate this recipe.")
        return

    # Prevent logged-in users from rating their own recipes
    if user_id == recipe_owner_id:
        st.info("You cannot rate your own recipe.")
        return

    # Retrieve the recipe owner's user_id
    recipe_owner_id = recipe["user_id"]

    # If the logged-in user is the owner of the recipe, don't allow rating
    if logged_in_user and recipe_owner_id == user_id:
        st.warning("You cannot rate your own recipe.")
        return

    # Retrieve the recipe owner's user_id
    recipe_owner_id = recipe["user_id"]

    # If the logged-in user is the owner of the recipe, don't allow rating
    if logged_in_user and recipe_owner_id == user_id:
        st.warning("You cannot rate your own recipe.")
        return

    # Rating input (always available for guest or non-owner logged-in users)
    st.write("Rate this recipe:")
    rating = st.slider("Your Rating", min_value=1, max_value=5, step=1)

    if st.button("Submit Rating"):
        # Check if the user has already rated
        existing_rating = ratings_collection.find_one({"recipe_id": recipe_id, "user_id": user_id})

        if existing_rating:
            # Update existing rating
            ratings_collection.update_one({"recipe_id": recipe_id, "user_id": user_id}, {"$set": {"rating": rating}})
            st.success("Your rating has been updated.")
        else:
            # Insert a new rating
            last_rating = ratings_collection.find_one(sort=[("rating_id", -1)])
            new_rating_id = last_rating["rating_id"] + 1 if last_rating else 1
            ratings_collection.insert_one({"rating_id": new_rating_id, "user_id": user_id, "recipe_id": recipe_id, "rating": rating})
            st.success("Thank you for rating this recipe!")

        # Recalculate and update the average rating in the Recipes collection
        all_ratings = ratings_collection.find({"recipe_id": recipe_id})
        total_ratings = [r["rating"] for r in all_ratings]
        avg_rating = sum(total_ratings) / len(total_ratings) if total_ratings else 0
        recipes_collection.update_one({"recipe_id": recipe_id}, {"$set": {"ratings": round(avg_rating, 1)}})
