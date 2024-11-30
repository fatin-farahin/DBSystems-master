# favorites.py

import streamlit as st
import pandas as pd
from db_connection import connect_db
from recipe_rating import display_rating

def add_to_favorites(user_id, recipe_id):
    db = connect_db()
    favorites_collection = db['favorites']

    # Ensure the recipe_id is correctly passed and not an ObjectId
    if not isinstance(recipe_id, int):  # Assuming recipe_id is an integer
        raise ValueError(f"recipe_id must be an integer, got {type(recipe_id)}: {recipe_id}")

    # Check if the recipe is already favorited by the user
    existing_favorite = favorites_collection.find_one({"user_id": user_id, "recipe_id": recipe_id})
    
    if existing_favorite:
        return "Recipe is already in your favorites."
    
    # Add the recipe to the favorites collection
    favorites_collection.insert_one({"user_id": user_id, "recipe_id": recipe_id})
    return "Recipe added to favorites!"

def remove_from_favorites(user_id, recipe_id):
    db = connect_db()
    favorites_collection = db['favorites']

    # Convert user_id and recipe_id to integers
    user_id = int(user_id)
    recipe_id = int(recipe_id)
    
    # Remove the favorite entry from the collection
    result = favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
    
    if result.deleted_count == 0:
        return "This recipe is not in your favorites."
    
    return "Recipe removed from favorites."

def toggle_favorite(user_id, recipe_id):
    # Add or remove a recipe from favorites depending on its current status
    db = connect_db()
    favorites_collection = db['favorites']

    # Convert user_id and recipe_id to integers
    user_id = int(user_id)
    recipe_id = int(recipe_id)
    
    # Check if the recipe is already favorited by the user
    existing_favorite = favorites_collection.find_one({"user_id": user_id, "recipe_id": recipe_id})
    
    if existing_favorite:
        # Remove from favorites if already in the list
        favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
        return "Removed from favorites."
    else:
        # Add to favorites if not in the list
        favorites_collection.insert_one({"user_id": user_id, "recipe_id": recipe_id})
        return "Added to favorites."

# Display Favorites
def show_favorites(user_id):
    db = connect_db()
    favorites_collection = db['favorites']
    recipes_collection = db['recipes']
    users_collection = db['users']

    # Query for the user's favorite recipes by their user_id
    favorite_recipes = list(favorites_collection.find({"user_id": user_id}))
    
    if not favorite_recipes:
        st.write("You have no favorite recipes.")
    else:
        st.write(f"Found {len(favorite_recipes)} favorite(s).")  # Debug statement
        for favorite in favorite_recipes:
            recipe_id = favorite['recipe_id']  # Ensure recipe_id is an integer
            # Query the recipes collection using recipe_id instead of ObjectId
            recipe = recipes_collection.find_one({"recipe_id": recipe_id})  # Search by recipe_id
            
            if recipe:
                if st.button(recipe['title'], key=f"recipe_button_{recipe['recipe_id']}"):
                    # Store the recipe_id in session_state to pass it to the recipe_details page
                    st.session_state.selected_recipe = recipe['recipe_id']
                    st.session_state.page = 'recipe_details'  # Navigate to the recipe details page
                    st.rerun()

                st.write(recipe['description'])

                # Get the username of the user who submitted the recipe
                recipe_user = users_collection.find_one({"user_id": recipe['user_id']})
                if recipe_user:
                    submitter_username = recipe_user['username']
                    # Create a clickable button for the submitter's username
                    if st.button(f"**Submitted by:** {submitter_username}", key=f"profile_button_{recipe['user_id']}_{recipe['recipe_id']}"):
                        # Navigate to the user profile
                        st.session_state.page = 'user_profile'  # Set the page to user_profile
                        st.session_state.viewing_username = submitter_username  # Track the user being viewed
                        st.rerun()

                # Display ratings as stars
                recipe_rating = recipe.get("ratings", None)  # Default to 0 if no rating exists
                rating_display = display_rating(recipe_rating)
                st.write(f"**Rating:** {rating_display}")
                
                # Button to remove the recipe from favorites
                if st.button(f"💔 Unfavorite", key=f"remove_{recipe['recipe_id']}"):
                    message = remove_from_favorites(user_id, recipe['recipe_id'])
                    st.success(message)
                st.write("---")