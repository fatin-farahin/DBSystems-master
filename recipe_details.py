# recipe_details.py

import streamlit as st
import os
from pymongo import MongoClient  # Import MongoDB client
from bson import ObjectId

# Function to connect to MongoDB
def connect_db():
    """Establish a connection to the MongoDB database."""
    client = MongoClient("mongodb://localhost:27017/")  # Connect to local MongoDB server
    db = client["inf2003_db"]  # Replace with your actual database name
    return db

# Fetch recipe details
def fetch_recipe_details(recipe_id):
    db = connect_db()

    try:
        # Convert recipe_id to ObjectId if needed
        recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})

        if not recipe:
            st.error("Recipe not found!")
            return None

        # Query recipe_info
        recipe_info = db.recipe_info.find_one({"recipeInfo_id": recipe["recipe_id"]})

        if not recipe_info:
            st.error("Recipe details not found!")
            return None

        # Retrieve username
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
    if 'selected_recipe' in st.session_state:
        recipe_id = st.session_state.selected_recipe
        recipe = fetch_recipe_details(recipe_id)

        if recipe:
            title, description, image_src, username, cook_time, servings, ingredients, instructions = recipe

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

            st.write("")  # Optional: smaller gap
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
            
            format_ingredients(ingredients)

            st.subheader("Instructions")
            st.write(instructions)

        if st.button("Back to Recipe List"):
            st.session_state.page = 'homepage'
            st.session_state.selected_recipe = None
            st.rerun()
    else:
        st.write("Recipe not found.")

# Format ingredients for display
def format_ingredients(ingredients):
    if isinstance(ingredients, str):  # Check if ingredients is a string
        # Split by commas and strip whitespace, then display each ingredient on a new line
        ingredient_list = [item.strip() for item in ingredients.split(",")]
    else:
        st.error("Ingredients format is invalid.")  # Show an error if it's not a string
        return
    
    section_name = "Ingredients"
    display_section(section_name, ingredient_list)

# Format instructions for display
def format_instructions(instructions):
    if isinstance(instructions, str):  # Check if instructions is a string
        # Split the instructions into individual steps by detecting periods followed by space
        instruction_list = instructions.split(". ")
        
        # Ensure no empty lines are present and strip any excess whitespace
        instruction_list = [step.strip() for step in instruction_list if step.strip()]
        
        # Add the period back to each instruction if missing
        instruction_list = [step + "." if not step.endswith('.') else step for step in instruction_list]
        
    else:
        st.error("Instructions format is invalid.")  # Show an error if it's not a string
        return

    section_name = "Instructions"
    display_section(section_name, instruction_list)

# Helper function to display a section with items
def display_section(section_name, items):
    st.subheader(section_name)
    
    num_items = len(items)

    # If the number of items is small, display them as a simple list
    if num_items <= 5:
        for item in items:
            st.write(f"- {item}")
    else:
        # For more than 5 items, display them in two columns
        cols = st.columns(2)
        
        for i in range(0, num_items, 2):
            with cols[0]:
                if i < num_items:
                    st.write(f"- {items[i]}")
            
            with cols[1]:
                if i + 1 < num_items:
                    st.write(f"- {items[i + 1]}")