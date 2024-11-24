# user_profile.py

import streamlit as st
import base64
import os
from bson.objectid import ObjectId
from db_connection import connect_db
from homepage import display_rating

# Fetch User Profile Data
def fetch_user_profile(username):
    db = connect_db()
    users_collection = db['users']
    user = users_collection.find_one({"username": username})
    return user

# Function to show the user profile page
def show_user_profile(username):
    # Get the logged-in username (if any)
    logged_in_username = st.session_state.get('username', None)

    # Fetch user profile information from MongoDB
    user = fetch_user_profile(username)

    if user:
        email = user.get('email', 'No email provided.')
        bio = user.get('bio', 'This user has not provided a bio yet.')
        profile_pic = user.get('profile_pic', None)
        dietary_preferences = user.get('dietary_id', None)

        # Fetch recipes shared by the user
        recipes = fetch_user_recipes(username)

        # Display user profile information
        st.markdown(f"""<h1 style="text-align: center;">{username}'s Profile</h1>""", unsafe_allow_html=True)

        # Display profile picture
        display_profile_picture(profile_pic)
        st.write("\n")

        # Display email, bio, dietary preferences, and recipe count
        st.write(f"**Email:** {email}")
        st.write(f"**Bio:** {bio}")
        st.write(f"**Dietary Preferences:** {fetch_dietary_name(dietary_preferences)}")

        # Allow editing if the logged-in user is viewing their own profile
        if logged_in_username == username:
            st.subheader("Edit Your Profile")
            new_bio = st.text_area("Edit your bio:", bio)
            new_profile_pic = st.text_input("Profile Picture Filename", profile_pic or "")
            
            # Fetch all dietary preferences for dropdown
            dietary_options = fetch_all_dietary_preferences()

            # Create a dropdown to select dietary preference
            new_dietary_preferences = st.selectbox(
                "Dietary Preferences", 
                options=list(dietary_options.values()), 
                index=list(dietary_options.values()).index(fetch_dietary_name(dietary_preferences))
            )

            # Get the corresponding dietary_id for the selected name
            selected_dietary_id = [diet_id for diet_id, diet_name in dietary_options.items() if diet_name == new_dietary_preferences][0]

            if st.button("Save Changes"):
                # Update the profile in MongoDB
                db = connect_db()
                db.users.update_one(
                    {"username": username},
                    {"$set": {
                        "bio": new_bio,
                        "profile_pic": new_profile_pic,
                        "dietary_id": selected_dietary_id
                    }}
                )
                st.success("Profile updated successfully!")
                st.rerun()

        # Display user's recipes
        st.subheader(f"{username}'s Recipes")
        if recipes:
            for recipe in recipes:
                # Display recipe details
                if st.button(f"{recipe['title']}", key=f"recipe_button_{recipe['recipe_id']}"):
                    # Store the recipe_id or title in session state to pass it to the recipe details page
                    st.session_state.selected_recipe = recipe['recipe_id']  # Store recipe ID
                    st.session_state.page = 'recipe_details'  # Navigate to the recipe details page
                    st.rerun()
                st.write(f"**Description:** {recipe['description']}")
                st.write(f"**Submitted by:** {username}")

                # Display ratings as stars
                recipe_rating = recipe.get("ratings", 0)  # Default to 0 if no rating exists
                rating_display = display_rating(recipe_rating)
                st.write(f"**Rating:** {rating_display}")
                st.write("---")
        else:
            st.write("No recipes found.")

        # Show favorites for the logged-in user's profile
        if logged_in_username == username:
            st.subheader("Your Favorite Recipes")
            show_favorites(username)
    else:
        st.error("User profile not found.")

# Save User Profile Data
def save_user_profile(username, new_username, new_email, new_bio, new_dietary_id):
    db = connect_db()
    users_collection = db['users']
    update = users_collection.update_one(
        {"username": username},
        {"$set": {
            "username": new_username,
            "email": new_email,
            "bio": new_bio,
            "dietary_id": new_dietary_id
        }}
    )
    if update.modified_count > 0:
        return "Profile updated successfully!"
    else:
        return "No changes made to the profile."
    
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
def save_recipe(title, description, cook_time, servings, ingredients, instructions, username):
    db = connect_db()
    recipes_collection = db['recipes']
    
    uploaded_file = st.file_uploader("Upload Recipe Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Create a directory for recipes if it doesn't exist
        recipe_folder = "uploads/recipes"
        if not os.path.exists(recipe_folder):
            os.makedirs(recipe_folder)

        # Save the image file in the "uploads/recipes" folder
        recipe_pic_path = os.path.join(recipe_folder, uploaded_file.name)
        with open(recipe_pic_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Add the image path to the recipe data
        new_recipe = {
            "title": title,
            "description": description,
            "cook_time": cook_time,
            "servings": servings,
            "ingredients": ingredients.splitlines(),
            "instructions": instructions.splitlines(),
            "user_id": username,
            "image_src": f"recipes/{uploaded_file.name}"  # Save relative path to the image
        }
        
        result = recipes_collection.insert_one(new_recipe)
        return f"Recipe added successfully with ID: {result.inserted_id}"

# Display Favorites
def show_favorites(username):
    db = connect_db()
    users_collection = db['users']
    user = users_collection.find_one({"username": username})
    favorite_recipe_ids = user.get('favorite_recipes', [])
    
    if favorite_recipe_ids:
        recipes_collection = db['recipes']
        recipes = recipes_collection.find({"_id": {"$in": [ObjectId(recipe_id) for recipe_id in favorite_recipe_ids]}})
        for recipe in recipes:
            st.write(f"**{recipe['title']}**")
            st.write(f"**Description:** {recipe['description']}")
            # Add buttons for actions on each recipe
    else:
        st.write("No favorite recipes found.")

# Toggle Favorite Status
def toggle_favorite(user_id, recipe_id):
    db = connect_db()
    users_collection = db['users']
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    favorites = user.get('favorite_recipes', [])
    
    if recipe_id in favorites:
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$pull": {"favorite_recipes": recipe_id}})
        st.success("Recipe removed from favorites!")
    else:
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$push": {"favorite_recipes": recipe_id}})
        st.success("Recipe added to favorites!")

# Display Profile Picture
def display_profile_picture(profile_pic):
    if profile_pic:
        profile_pic_path = f"uploads/users/{profile_pic}"
        
        # Check if the profile picture file exists
        if os.path.exists(profile_pic_path):
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{base64.b64encode(open(profile_pic_path, "rb").read()).decode()}"
                    style="width: 250px; height: 250px; border-radius: 50%; object-fit: cover;" 
                    alt="Profile Picture">
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Display default profile picture if the user's profile picture doesn't exist
            show_default_profile_picture()
    else:
        # Display default profile picture if no profile picture is provided
        show_default_profile_picture()

def show_default_profile_picture():
    default_picture_path = "uploads/users/defaultprofile.png"
    if os.path.exists(default_picture_path):
        st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{base64.b64encode(open(default_picture_path, "rb").read()).decode()}"
                    style="width: 250px; height: 250px; border-radius: 50%; object-fit: cover;" 
                    alt="Profile Picture">
                </div>
                """,
                unsafe_allow_html=True
            )
        
# Upload Profile Picture
def upload_profile_picture(username):
    db = connect_db()
    users_collection = db["users"]

    uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Create a directory for the user if it doesn't exist
        user_folder = f"uploads/users"
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # Save the image file in the user's folder
        profile_pic_path = os.path.join(user_folder, uploaded_file.name)
        with open(profile_pic_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Update MongoDB with the relative file path
        users_collection.update_one(
            {"username": username},
            {"$set": {"profile_pic": uploaded_file.name}}  # Only store the filename in MongoDB
        )

        st.success("Profile picture updated!")

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
                if st.button(recipe["title"], key=f"recipe_{recipe['_id']}"):
                    st.session_state.selected_recipe = recipe["_id"]
                    st.session_state.page = "recipe_details"
                st.write(f"**Description:** {recipe['description']}")
                st.write("---")
    else:
        st.write("This user has not submitted any recipes yet.")

# Edit and Update Recipe
def show_edit_recipe_form(recipe_id):
    db = connect_db()
    recipes_collection = db["recipes"]

    recipe = recipes_collection.find_one({"_id": recipe_id})
    if recipe:
        updated_title = st.text_input("Recipe Title", value=recipe["title"])
        updated_description = st.text_area("Recipe Description", value=recipe["description"])
        updated_cook_time = st.number_input("Cook Time (minutes)", value=recipe["cook_timeserving"], min_value=1)
        updated_servings = st.number_input("Servings", value=recipe["servings"], min_value=1)
        updated_ingredients = st.text_area("Ingredients", value=recipe["ingredients"])
        updated_instructions = st.text_area("Instructions", value=recipe["instructions"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Recipe"):
                recipes_collection.update_one(
                    {"_id": recipe_id},
                    {"$set": {
                        "title": updated_title,
                        "description": updated_description,
                        "cook_timeserving": updated_cook_time,
                        "servings": updated_servings,
                        "ingredients": updated_ingredients,
                        "instructions": updated_instructions
                    }}
                )
                st.success("Recipe updated successfully!")
        with col2:
            if st.button("Cancel"):
                st.session_state.selected_recipe = None

# Delete Recipe
def delete_recipe(recipe_id):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_ratings_collection = db["recipe_ratings"]

    recipe_ratings_collection.delete_many({"recipe_id": recipe_id})
    recipes_collection.delete_one({"_id": recipe_id})
    st.success("Recipe deleted successfully!")

# Update Profile
def update_profile(username, new_username, new_email, new_bio, new_dietary_id):
    db = connect_db()
    users_collection = db["users"]

    user = users_collection.find_one({"username": username})
    if user:
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "username": new_username,
                "email": new_email,
                "bio": new_bio,
                "dietary_id": new_dietary_id
            }}
        )
        st.success("Profile updated successfully!")
    else:
        st.error("User not found.")