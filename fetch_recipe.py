# fetch_recipe.py

import streamlit as st
import os
from db_connection import connect_db
from homepage import display_rating, remove_from_favorites

def show_edit_recipe():
    st.subheader("Edit Your Recipes")
    logged_in_username = st.session_state.get("username") # Get the logged-in username (if any)
    recipes = fetch_user_recipes(logged_in_username)  # Fetch user's recipes from database

    if recipes:
        # Create a dropdown to select a recipe
        recipe_titles = [recipe['title'] for recipe in recipes]
        selected_recipe_title = st.selectbox("Select a recipe to edit", recipe_titles)

        # Find the selected recipe from the list
        selected_recipe = next(recipe for recipe in recipes if recipe['title'] == selected_recipe_title)

        # Show the recipe form if a recipe is selected
        if selected_recipe:
            if st.button(f"Edit {selected_recipe['title']}"):
                st.session_state.selected_recipe = selected_recipe['recipe_id']  # Store the recipe ID in session state
                st.session_state.page = 'edit_recipe'  # Navigate to edit_recipe page
                st.rerun()
    else:
        st.write("No recipes found to edit.")

def show_add_recipe():
    st.subheader("Add Your Recipes")
    db = connect_db()
    dietary_collection = db["dietary"]  # Collection for dietary preferences
    cuisines_collection = db["cuisines"]  # Collection for cuisines
    users_collection = db["users"]  # Collection for users

    logged_in_username = st.session_state.get("username")  # Get the logged-in username (if any)

    # Fetch the user from the users collection to get user_id (assuming it's stored as integer user_id)
    user = users_collection.find_one({"username": logged_in_username})
    if user:
        user_id = user.get("user_id")  # Use the integer user_id directly (instead of _id)
    else:
        st.error("User not found.")
        return  # Exit if the user is not found
    
    # Initialize image_file_name to avoid UnboundLocalError
    image_file_name = ""  # Default to an empty string

    # Recipe form for adding a new recipe
    st.session_state.show_recipe_form = True

    if st.session_state.get('show_recipe_form', False):
        # Define recipe fields
        new_recipe_title = st.text_input("Recipe Title", key="new_recipe_title")
        new_recipe_description = st.text_area("Recipe Description", key="new_recipe_description")
        new_cook_time = st.number_input("Cook Time (minutes)", min_value=1, key="new_cook_time")
        new_servings = st.number_input("Servings", min_value=1, key="new_servings")
        new_ingredients = st.text_area("Ingredients (one per line)", key="new_ingredients")
        new_instructions = st.text_area("Instructions (one per line)", key="new_instructions")

        # Fetch dietary options from MongoDB
        dietary_options = dietary_collection.find()  # Fetch dietary preferences
        dietary_dict = {diet['name']: str(diet['dietary_id']) for diet in dietary_options}  # Mapping name to dietary_id

        # Fetch cuisine options from MongoDB
        cuisine_options = cuisines_collection.find()  # Fetch cuisine options
        cuisine_dict = {cuisine['name']: str(cuisine['cuisine_id']) for cuisine in cuisine_options}  # Mapping name to cuisine_id

        col1, col2 = st.columns(2)
        with col1:
            new_dietary_name = st.selectbox("Dietary Preferences", list(dietary_dict.keys()), key="new_dietary")
            new_dietary_id = dietary_dict.get(new_dietary_name)  # Get dietary_id based on selected name

        with col2:
            new_cuisine_name = st.selectbox("Cuisine Type", list(cuisine_dict.keys()), key="new_cuisine")
            new_cuisine_id = cuisine_dict.get(new_cuisine_name)  # Get cuisine_id based on selected name

        # Image upload
        uploaded_image = st.file_uploader("Upload Recipe Image", type=["jpeg", "jpg", "png"], key="recipe_image")
        if uploaded_image is not None:
            image_file_name = f"{uploaded_image.name}"
            image_file_path = f"uploads/recipes/{image_file_name}"

            with open(image_file_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            st.success(f"Image '{uploaded_image.name}' uploaded successfully.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Recipe", key="submit_recipe_button"):
                message = save_recipe(
                    new_recipe_title,
                    new_recipe_description,
                    new_cook_time,
                    new_servings,
                    new_ingredients,
                    new_instructions,
                    user_id,  # Pass the integer user_id
                    image_file_name if image_file_name else "", # Default to empty string if no image
                    new_dietary_id,  # Pass the dietary_id
                    new_cuisine_id  # Pass the cuisine_id
                )
                st.success(message)
                st.session_state.show_recipe_form = False  # Hide the recipe form
                st.session_state.page = "user_profile"  # Redirect to Select Recipe page
                st.rerun()

        with col2:
            if st.button("Cancel", key="cancel_recipe_button"):
                st.session_state.show_recipe_form = False  # Hide the form when cancel is clicked
                st.session_state.page = "user_profile"  # Redirect to Select Recipe page
                st.rerun()

# Show Recipes
def show_my_recipes(username):
    db = connect_db()
    users_collection = db["users"]
    recipes_collection = db["recipes"]

    user = users_collection.find_one({"username": username})
    if user:
        recipes = recipes_collection.find({"user_id": user["_id"]})
        cols = st.columns(2)  # Create 2 columns for layout
        for i, recipe in enumerate(recipes):
            with cols[i % 2]:  # Use modulo to alternate between columns
                # Convert ObjectId to string when storing in session_state
                if st.button(recipe["title"], key=f"recipe_{recipe['recipe_id']}"):
                    st.session_state.selected_recipe = recipe["recipe_id"] 
                    st.session_state.page = "edit_recipe"
                    st.rerun()
                st.write(f"**Description:** {recipe['description']}")
                st.write("---")
    else:
        st.write("This user has not submitted any recipes yet.")

# Edit and Update Recipe
def show_edit_recipe_form(recipe_id):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_info_collection = db["recipe_info"]
    cuisines_collection = db["cuisines"]
    dietary_collection = db["dietary"]

    # Fetch the recipe
    recipe = recipes_collection.find_one({"recipe_id": recipe_id})
    recipe_info = recipe_info_collection.find_one({"recipeInfo_id": recipe_id})

    if recipe and recipe_info:
        # Fetch cuisines and dietary options
        cuisines = list(cuisines_collection.find())  # Convert cursor to list
        dietary_options = list(dietary_collection.find())  # Convert cursor to list

        # Prepare lists for the selectbox options
        cuisine_names = [cuisine["name"] for cuisine in cuisines]
        dietary_names = [dietary["name"] for dietary in dietary_options]

        # Get the current dietary and cuisine IDs from the recipe
        current_dietary_id = recipe.get("dietary_id", None)
        current_cuisine_id = recipe.get("cuisine_id", None)

        # Get the current dietary and cuisine names based on their IDs
        current_dietary_name = next(
            (dietary["name"] for dietary in dietary_options if dietary["dietary_id"] == current_dietary_id),
            None
        )

        current_cuisine_name = next(
            (cuisine["name"] for cuisine in cuisines if cuisine["cuisine_id"] == current_cuisine_id),
            None
        )

        # Default to the first option if the current ID is not found
        if current_cuisine_name is None:
            current_cuisine_name = cuisine_names[0] if cuisine_names else None
        if current_dietary_name is None:
            current_dietary_name = dietary_names[0] if dietary_names else None

        # Input fields for editing
        updated_title = st.text_input("Recipe Title", value=recipe.get("title", ""))
        updated_description = st.text_area("Recipe Description", value=recipe.get("description", ""))
        updated_cook_time = st.number_input(
            "Cook Time (minutes)", value=recipe_info.get("cook_timeserving", 1), min_value=1
        )
        updated_servings = st.number_input(
            "Servings", value=recipe_info.get("servings", 1), min_value=1
        )
        updated_ingredients = st.text_area("Ingredients", value=recipe_info.get("ingredients", ""))
        updated_instructions = st.text_area("Instructions", value=recipe_info.get("instructions", ""))

        # Select boxes for dietary and cuisine with safe handling
        updated_dietary = st.selectbox("Select Dietary", options=dietary_names, index=dietary_names.index(current_dietary_name) if current_dietary_name in dietary_names else 0)
        updated_cuisine = st.selectbox("Select Cuisine", options=cuisine_names, index=cuisine_names.index(current_cuisine_name) if current_cuisine_name in cuisine_names else 0)

        # Find the corresponding ids from the selected names, with fallback default if no match found
        new_dietary_id = next((dietary["dietary_id"] for dietary in dietary_options if dietary["name"] == updated_dietary), None)
        new_cuisine_id = next((cuisine["cuisine_id"] for cuisine in cuisines if cuisine["name"] == updated_cuisine), None)

        # Handle case where no matching dietary or cuisine is found
        if new_dietary_id is None:
            new_dietary_id = dietary_options[0]["dietary_id"] if dietary_options else None
        if new_cuisine_id is None:
            new_cuisine_id = cuisines[0]["cuisine_id"] if cuisines else None

        # Upload recipe picture
        uploaded_image = st.file_uploader(
            "Upload a new picture for the recipe", type=["png", "jpg", "jpeg"]
        )
        if uploaded_image:
            image_path = f"uploads/recipes/{uploaded_image.name}"
            with open(image_path, "wb") as f:
                f.write(uploaded_image.read())
            st.image(uploaded_image, caption="Uploaded recipe picture", width=300)
        else:
            # If no image is uploaded, show the current image
            if recipe.get("image_src"):
                current_image_path = f"uploads/recipes/{recipe['image_src']}"
                if os.path.exists(current_image_path):
                    st.image(current_image_path, caption="Current Recipe Picture", width=200)
                else:
                    st.warning("Current image not found or failed to load.")

        # Buttons for Update, Delete, and Cancel
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Update Recipe", key="update_button"):
                # Prepare the update fields
                update_fields = {
                    "title": updated_title,
                    "description": updated_description
                }
                
                if uploaded_image:
                    # If a new image is uploaded, update the image_src field
                    update_fields["image_src"] = uploaded_image.name
                    # Optionally remove the old image if it's replaced
                    if recipe.get("image_src") and recipe['image_src'] != uploaded_image.name:
                        old_image_path = f"uploads/recipes/{recipe['image_src']}"
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                # Update the recipes collection
                recipes_collection.update_one(
                    {"recipe_id": recipe_id},
                    {"$set": update_fields}
                )

                # Prepare the update fields for the recipe_info collection
                update_fields_recipe_info = {
                    "dietary_id": new_dietary_id,
                    "cuisine_id": new_cuisine_id,
                    "cook_timeserving": updated_cook_time,
                    "servings": updated_servings,
                    "ingredients": updated_ingredients,
                    "instructions": updated_instructions,
                }

                # Update the recipe_info collection
                recipe_info_collection.update_one(
                    {"recipeInfo_id": recipe_id},  # Match by recipeInfo_id
                    {"$set": update_fields_recipe_info}
                )
                st.success("Recipe updated successfully!")
                st.session_state.selected_recipe = None
                st.session_state.page = "select_recipe"  # Navigate back to profile
                st.rerun()

        with col2:
            if st.button("Cancel", key="cancel_button"):
                # Navigate to the page where the user can select a recipe
                st.session_state.selected_recipe = None
                st.session_state.page = "select_recipe"  # Redirect to Select Recipe page
                st.rerun()

        with col3:
            # When Delete Recipe button is clicked
            if st.button("Delete Recipe", key="delete_button"):
                # Show a warning prompt before deletion
                st.warning("Are you sure you want to delete this recipe? This action cannot be undone.")
                st.session_state.confirm_delete = True  # Set confirmation to True after the warning

            # Show the "Confirm Delete" button only if confirm_delete is True
            if st.session_state.confirm_delete:
                if st.button("Confirm Delete", key="confirm_delete_button"):
                    # If confirmed, delete the recipe
                    delete_recipe(recipe_id=recipe["recipe_id"], image_file_name=recipe.get("image_src"))
                    st.success("Recipe deleted successfully!")
                    st.session_state.selected_recipe = None  # Reset selected recipe after deletion
                    st.session_state.page = "select_recipe"  # Redirect to recipe selection page
                    st.session_state.confirm_delete = False  # Reset confirmation state

            # Cancel button logic (if you want to cancel the delete operation)
            if st.session_state.confirm_delete and st.button("Cancel", key="cancel_delete_button"):
                st.session_state.confirm_delete = False  # Reset confirm_delete to False
                st.session_state.page = "select_recipe"  # Go back to the recipe selection page
                st.rerun()

    else:
        st.error("Recipe not found!")

# Delete Recipe
def delete_recipe(recipe_id, image_file_name=None):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_info_collection = db["recipe_info"]

    # Ensure that recipe_id is of the correct type (int, based on your data structure)
    if isinstance(recipe_id, str):
        recipe_id = int(recipe_id)
    
    # Fetch the recipe and recipe_info to ensure they exist
    recipe = recipes_collection.find_one({"recipe_id": recipe_id})
    recipe_info = recipe_info_collection.find_one({"recipeInfo_id": recipe_id})

    if recipe:
        # Delete the recipe from the 'recipes' collection
        recipes_collection.delete_one({"recipe_id": recipe_id})
        
        # Delete the corresponding recipe_info from the 'recipe_info' collection
        recipe_info_collection.delete_one({"recipeInfo_id": recipe_id})

        # Delete associated image file if exists
        if image_file_name:
            image_path = f"uploads/recipes/{image_file_name}"
            if os.path.exists(image_path):
                os.remove(image_path)

# Fetch all dietary preferences for the dropdown list
def fetch_all_dietary_preferences():
    db = connect_db()
    dietary_collection = db["dietary"]
    # Fetch all dietary preferences from the dietary collection
    dietary_list = dietary_collection.find()
    return {diet["dietary_id"]: diet["name"] for diet in dietary_list}
    
# Fetch Dietary Name
def fetch_dietary_name(dietary_id):
    db = connect_db()
    dietary_collection = db["dietary"]
        
    dietary = dietary_collection.find_one({"dietary_id": dietary_id})
    return dietary["name"] if dietary else "None"

# Fetch User's Recipes
def fetch_user_recipes(username):
    db = connect_db()
    recipes_collection = db['recipes']
    users_collection = db['users']
    
    # Fetch the user from the users collection
    user = users_collection.find_one({"username": username})
    if not user:
        return []  # Return an empty list if user is not found

    user_id = user.get('user_id')  # Get the user_id from the user document
    if not user_id:
        return []  # Return an empty list if user_id is not found
    
    # Fetch recipes by user_id
    recipes = list(recipes_collection.find({"user_id": user_id}))
    
    return recipes

# Save Recipe to MongoDB
def save_recipe(title, description, cook_timeserving, servings, ingredients, instructions, user_id, image_file_name, dietary, cuisine):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_info_collection = db["recipe_info"]

    # Generate the next `recipe_id` for the entire collection (across all users)
    last_recipe = list(recipes_collection.find().sort("recipe_id", -1).limit(1))
    if last_recipe:
        max_recipe_id = last_recipe[0]["recipe_id"]
    else:
        max_recipe_id = 0  # If no recipes exist, start with 0
    new_recipe_id = max_recipe_id + 1  # Increment for the new recipe

    # Insert into recipes collection
    new_recipe = {
        "recipe_id": new_recipe_id,  # Sequential recipe_id for this user
        "title": title,
        "description": description,
        "image_src": image_file_name,
        "ratings": None,  # Ratings can be set to None initially
        "user_id": user_id,  # Ensure user_id is passed as integer
    }
    recipes_collection.insert_one(new_recipe)

    # Insert into recipe_info collection and link to the recipe_id
    new_recipe_info = {
        "recipeInfo_id": new_recipe_id,  # Use the same recipe_id for consistency
        "cook_timeserving": cook_timeserving,
        "servings": servings,
        "ingredients": ingredients,  # Ensure ingredients are correctly formatted
        "instructions": instructions,  # Ensure instructions are correctly formatted
        "dietary_id": dietary,  # Set the dietary_id
        "cuisine_id": cuisine,  # Set the cuisine_id
    }
    recipe_info_collection.insert_one(new_recipe_info)

    return f"Recipe '{title}' saved successfully."
    
def display_recipe_image(image_src):
    if image_src:
        image_path = f"uploads/recipes"
        
        # Check if the image file exists
        if os.path.exists(image_path):
            st.image(image_path, use_column_width=True)
        else:
            # If the file doesn't exist, show a placeholder or default image
            st.error("Recipe image not found. Displaying default image.")
            st.image("uploads/defaultrecipe.png", use_column_width=True)