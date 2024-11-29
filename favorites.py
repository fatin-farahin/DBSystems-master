import streamlit as st
import base64
import os
from db_connection import connect_db
from homepage import display_rating, remove_from_favorites

# Display Favorites
def show_favorites(username):
    db = connect_db()
    users_collection = db['users']
    favorites_collection = db['favorites']
    recipes_collection = db['recipes']

    # Find user by username
    user = users_collection.find_one({"username": username})
    
    if user:
        user_id = user.get("user_id")
        
        # Query the favorites collection to find all favorite recipes for this user
        favorite_recipes = favorites_collection.find({"user_id": user_id})
        
        if favorite_recipes:
            for favorite in favorite_recipes:
                recipe_id = int(favorite['recipe_id'])  # Ensure recipe_id is an integer
                
                # Find the recipe details based on the recipe_id
                recipe = recipes_collection.find_one({"recipe_id": recipe_id})
                
                if recipe:
                    st.write(f"**{recipe['title']}**")
                    st.write(f"**Description:** {recipe['description']}")
                    
                    # Look up the user who submitted the recipe
                    recipe_user = users_collection.find_one({"user_id": recipe['user_id']})
                    if recipe_user:
                        st.write(f"**Submitted by:** {recipe_user['username']}")
                    
                    # Button to unfavorite the recipe
                    if st.button(f"💔 Unfavorite", key=f"unfavorite_{recipe['recipe_id']}"):
                        favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
                        toggle_favorite(user_id, recipe_id)  # Use toggle function to update favorites
                    st.write("---")
                else:
                    st.write("Recipe not found.")
        else:
            st.write("No favorite recipes found.")
    else:
        st.write("User not found.")

# Toggle Favorite Status
def toggle_favorite(user_id, recipe_id):
    db = connect_db()
    favorites_collection = db["favorites"]

    # Ensure recipe_id is treated as an integer
    recipe_id = int(recipe_id)
    
    # Check if this user has already favorited the recipe
    favorite = favorites_collection.find_one({"user_id": user_id, "recipe_id": recipe_id})
    
    if favorite:
        # If found, remove it from the favorites collection
        favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
        st.success("Recipe removed from favorites!")
    else:
        # If not found, add it to the favorites collection with recipe_id as _id
        favorite_data = {
            "user_id": user_id,
            "recipe_id": recipe_id
        }
        
        # Insert the favorite into the collection
        favorites_collection.insert_one(favorite_data)
        st.success("Recipe added to favorites!")
    st.rerun()