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

def rate_recipe(recipe_id, recipe_creator_id):
    db = connect_db()
    ratings_collection = db["recipe_ratings"]
    recipes_collection = db["recipes"]

    try:
        # Check if the user is logged in
        user_id = st.session_state.get("logged_in_user", {}).get("user_id", None)

        # Prevent logged-in users from rating their own recipes
        if user_id and user_id == recipe_creator_id:
            st.info("You cannot rate your own recipe.")
            return

        # Show rating input (1 to 5 stars)
        st.write("Rate this recipe:")
        rating = st.slider("Your Rating", min_value=1, max_value=5, step=1)

        if st.button("Submit Rating"):
            # For guest users, use `user_id=None`
            if not user_id:
                user_id = None

            # Check if the guest user or logged-in user has already rated the recipe
            existing_rating = ratings_collection.find_one({"recipe_id": recipe_id, "user_id": user_id})
            if existing_rating:
                ratings_collection.update_one(
                    {"recipe_id": recipe_id, "user_id": user_id},
                    {"$set": {"rating": rating}}
                )
                st.success("Your rating has been updated.")
            else:
                # Generate a new `rating_id` (incremental integer)
                rating_id = ratings_collection.count_documents({}) + 1
                ratings_collection.insert_one({
                    "rating_id": rating_id,
                    "user_id": user_id,
                    "recipe_id": recipe_id,
                    "rating": rating
                })
                st.success("Thank you for rating this recipe!")

            # Recalculate average rating for the recipe
            all_ratings = ratings_collection.find({"recipe_id": recipe_id})
            total_ratings = [r["rating"] for r in all_ratings]
            avg_rating = sum(total_ratings) / len(total_ratings) if total_ratings else 0

            # Update the average rating in the Recipes collection
            recipes_collection.update_one(
                {"recipe_id": recipe_id},
                {"$set": {"ratings": round(avg_rating, 1)}}
            )

    except Exception as e:
        st.error(f"An error occurred while rating the recipe: {e}")
