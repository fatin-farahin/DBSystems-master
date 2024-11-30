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
            recipe["user_id"],
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
            title, description, image_src, username, recipe_creator_id, cook_time, servings, ingredients, instructions = recipe

            st.title(title)

            image_path = f"uploads/recipes/{image_src}"

            st.markdown("""
                <style>
                .recipe-image img {
                    max-width: 400px;
                    width: 100%;
                    height: auto;
                }
                </style>
            """, unsafe_allow_html=True)

            # Display the recipe image
            if os.path.exists(image_path):
                st.image(image_path, width=300)
            else:
                st.write("Image not found.")

            st.write(f"**Description:** {description}")
            st.write(f"**Cook Time:** {cook_time} minutes")
            st.write(f"**Servings:** {servings}")

            # Display the username as a clickable link
            if st.button(f"Submitted by: {username}", key=f"user_{username}_{recipe_id}"):
                st.session_state.page = 'user_profile'
                st.session_state.viewing_username = username
                st.rerun()

            st.write("")
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
            
            st.subheader("Ingredients")
            format_ingredients(ingredients)

            st.subheader("Instructions")
            format_instructions(instructions)
            st.write("")

            # Add rating functionality
            rate_recipe(recipe_id, recipe_creator_id)

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