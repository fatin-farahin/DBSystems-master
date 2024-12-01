# recipe_details.py

import streamlit as st
import os
from db_connection import connect_db
from recipe_rating import rate_recipe

# Fetch recipe details
def fetch_recipe_details(recipe_id):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_info_collection = db["recipe_info"]

    try:
        # Ensure recipe_id is an integer
        recipe_id = int(recipe_id)
        
        # Query for the recipe from the recipes collection
        recipe = recipes_collection.find_one({"recipe_id": recipe_id})

        if not recipe:
            st.error("Recipe not found!")
            return None
        
        # Query for recipe details from the recipe_info collection
        recipe_info = recipe_info_collection.find_one({"recipeInfo_id": recipe["recipe_id"]})

        if not recipe_info:
            st.error(f"Recipe details not found!")
            return None

        # Retrieve the username
        user_dict = st.session_state.get("user_dict", {})
        user_name = user_dict.get(str(recipe["user_id"]), "Unknown")
        
        return (
            recipe["title"],
            recipe["description"],
            recipe["image_src"],
            user_name,
            recipe_info["cook_timeserving"],
            recipe_info["servings"],
            recipe_info["ingredients"],
            recipe_info["instructions"]
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Recipe details page
def recipe_details():
    db = connect_db()
    recipes_collection = db["recipes"]

    if 'selected_recipe' in st.session_state:
        recipe_id = st.session_state.selected_recipe
        recipe = fetch_recipe_details(recipe_id)

        if recipe:
            title, description, image_src, username, cook_time, servings, ingredients, instructions = recipe

            # Display recipe details
            st.title(title)
            st.image(f"uploads/recipes/{image_src}", width=300)
            st.write(f"**Description:** {description}")
            st.write(f"**Cook Time:** {cook_time} minutes")
            st.write(f"**Servings:** {servings}")

            # Display ingredients and instructions
            st.subheader("Ingredients")
            format_ingredients(ingredients)
            st.subheader("Instructions")
            format_instructions(instructions)

            # Check if the user is logged in
            logged_in_user = st.session_state.get('logged_in_user')

            if logged_in_user:
                logged_in_user_id = logged_in_user["user_id"]
                recipe_owner_id = recipe[3]  # recipe_owner is the 4th item in the recipe tuple

                # If logged-in user is the owner, don't allow rating
                if logged_in_user_id == recipe_owner_id:
                    st.info("You cannot rate your own recipe.")
                else:
                    rate_recipe(recipe_id)  # Allow rating for non-owners
            else:
                rate_recipe(recipe_id)  # Allow rating for guest users

        if st.button("Back to Recipe List"):
            st.session_state.page = 'homepage'
            st.session_state.selected_recipe = None
            st.rerun()
    else:
        st.write("Recipe not found.")

# Format ingredients for display
def format_ingredients(ingredients):
    if isinstance(ingredients, str):
        # Split ingredients by newlines
        ingredient_list = [ingredient.strip() for ingredient in ingredients.split("\n")] 
        
        # Render the ingredients as bullet points
        display_section("Ingredients", ingredient_list, bullet=True)
    else:
        st.error("Ingredients format is invalid.")
        return

# Format instructions for display
def format_instructions(instructions):
    if isinstance(instructions, str):
        # Split instructions by newlines
        instruction_list = [instruction.strip() for instruction in instructions.split("\n")]
        
        # Render the instructions as numbered points
        display_section("Instructions", instruction_list, bullet=False)
    else:
        st.error("Instructions format is invalid.")
        return

# Helper function to display a section with items
def display_section(section_name, content_list, bullet=False):
    # Display content based on whether it's a bullet list
    if bullet:
        for item in content_list:
            st.markdown(f"• {item}")
    else:
        # For non-bullet content (e.g., numbered list or plain paragraphs)
        for i, item in enumerate(content_list, start=1):
            st.markdown(f"{i}. {item}")  # Numbered list for instructions