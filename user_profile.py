# user_profile.py

import streamlit as st
import base64
import os
from bson.objectid import ObjectId
from db_connection import connect_db
from homepage import display_rating, remove_from_favorites

# Fetch User Profile Data
def fetch_user_profile(username):
    db = connect_db()
    users_collection = db['users']
    user = users_collection.find_one({"username": username})
    return user

# Function to show the user profile page
def show_user_profile(username):
    # Get the logged-in username (if any)
    logged_in_username = st.session_state.get("username")

    # If a username is passed in the URL or function, use that; otherwise, use logged-in username
    profile_username = username if username else logged_in_username

    # Fetch user profile information from MongoDB
    user = fetch_user_profile(profile_username)

    if user:
        email = user.get('email', 'No email provided.')
        bio = user.get('bio', 'This user has not provided a bio yet.')
        profile_pic = user.get('profile_pic', None)
        dietary_preferences = user.get('dietary_id', None)

        # Allow editing if the logged-in user is viewing their own profile
        if logged_in_username == profile_username:
            section = st.sidebar.selectbox("Choose an option", ["View Profile", "Update Profile", "Edit Recipes", "Favorites"])

            if section == 'Update Profile':
                st.subheader("Edit Your Profile")
                new_username = st.text_input("Username", logged_in_username)  # Default value is the current username
                new_email = st.text_input("Email", email)
                new_bio = st.text_area("Bio:", bio)

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

                # Profile picture upload section (file upload widget)
                new_profile_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])

                # Check if a new profile picture is uploaded
                if new_profile_pic:
                    # Optionally display the uploaded image
                    st.image(new_profile_pic, caption="Uploaded profile picture", use_column_width=True)

                if st.button("Save Changes"):
                    result = update_user_profile(
                        logged_in_username,  # Old username
                        new_username,        # New username
                        new_email,
                        new_bio,
                        selected_dietary_id,
                        new_profile_pic
                    )
                    
                    if isinstance(result, dict) and result.get("status") == "success":
                        st.success("Profile updated successfully!")
                        # Update session state with new username
                        st.session_state["username"] = new_username
                        logged_in_username = new_username  # Update logged-in username immediately
                        # Refetch the user's profile to reflect updates
                        user = fetch_user_profile(logged_in_username)
                        st.rerun()  # Reload the page with the new username
                    else:
                        st.error(result)

            elif section == 'Edit Recipes':
                db = connect_db()
                dietary_collection = db["dietary"]  # Collection for dietary preferences
                cuisines_collection = db["cuisines"]  # Collection for cuisines
                
                st.subheader("Edit Your Recipes")
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
                            st.session_state.selected_recipe = selected_recipe['recipe_id']
                            show_edit_recipe_form(selected_recipe['recipe_id'])  # Pass the selected recipe_id
                            st.session_state.page = 'edit_recipe'  # Set the page to show the edit form
                else:
                    st.write("No recipes found to edit.")

                # Recipe form for adding a new recipe
                add_recipe_button = st.button("Add Recipe", key="add_recipe_button")
                if add_recipe_button:
                    st.session_state.show_recipe_form = True

                if st.session_state.get('show_recipe_form', False):
                    # Define recipe fields
                    new_recipe_title = st.text_input("Recipe Title", key="new_recipe_title")
                    new_recipe_description = st.text_area("Recipe Description", key="new_recipe_description")
                    new_cook_time = st.number_input("Cook Time (minutes)", min_value=1, key="new_cook_time")
                    new_servings = st.number_input("Servings", min_value=1, key="new_servings")
                    new_ingredients = st.text_area("Ingredients (one per line)", key="new_ingredients")
                    new_instructions = st.text_area("Instructions", key="new_instructions")

                    # Fetch dietary options from MongoDB
                    dietary_options = dietary_collection.find()  # Fetch dietary preferences
                    dietary_dict = {str(diet['dietary_id']): diet['name'] for diet in dietary_options}

                    col1, col2 = st.columns(2)
                    with col1:
                        new_dietary = st.selectbox("Dietary Preferences", list(dietary_dict.values()), key="new_dietary")

                    # Fetch cuisine options from MongoDB
                    cuisine_options = cuisines_collection.find()  # Fetch cuisine options
                    cuisine_dict = {str(cuisine['cuisine_id']): cuisine['name'] for cuisine in cuisine_options}

                    with col2:
                        new_cuisine = st.selectbox("Cuisine Type", list(cuisine_dict.values()), key="new_cuisine")

                    # Image upload
                    uploaded_image = st.file_uploader("Upload Recipe Image", type=["jpeg", "jpg", "png"], key="recipe_image")
                    if uploaded_image is not None:
                        image_file_name = f"{logged_in_username}_{new_recipe_title}_{uploaded_image.name}"
                        image_file_path = f"recipes/uploads/recipe_images/{image_file_name}"

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
                                logged_in_username,
                                image_file_name,
                                new_dietary,
                                new_cuisine
                            )
                            st.success(message)
                            st.session_state.show_recipe_form = False
                    with col2:
                        if st.button("Cancel", key="cancel_recipe_button"):
                            st.session_state.show_recipe_form = False

            elif section == 'Favorites':
                st.subheader("Your Favorite Recipes")
                show_favorites(username)

            else:
                # Default "View Profile" section
                st.markdown(f"""<h1 style="text-align: center;">{username}'s Profile</h1>""", unsafe_allow_html=True)
                
                # Display profile picture
                display_profile_picture(profile_pic)
                st.write("\n")

                # Display email, bio, dietary preferences, and recipe count
                st.write(f"**Email:** {email}")
                st.write(f"**Bio:** {bio}")
                st.write(f"**Dietary Preferences:** {fetch_dietary_name(dietary_preferences)}")

                # Fetch recipes shared by the user
                recipes = fetch_user_recipes(logged_in_username)
                if recipes:
                    st.subheader(f"{username}'s Recipes")
                    for recipe in recipes:
                        # Display recipe details
                        if st.button(f"{recipe['title']}", key=f"recipe_button_{recipe['recipe_id']}"):
                            # Ensure recipe_id is converted to string if it is an integer
                            st.session_state.selected_recipe = recipe['recipe_id']  # Store recipe_id as integer
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
        else:
            # Show only profile info for other users
            st.markdown(f"""<h1 style="text-align: center;">{username}'s Profile</h1>""", unsafe_allow_html=True)
            
            # Display profile picture
            display_profile_picture(profile_pic)
            st.write("\n")

            # Display email, bio, dietary preferences, and recipe count
            st.write(f"**Email:** {email}")
            st.write(f"**Bio:** {bio}")
            st.write(f"**Dietary Preferences:** {fetch_dietary_name(dietary_preferences)}")
            
            # Fetch recipes shared by the user
            recipes = fetch_user_recipes(profile_username)
            if recipes:
                st.subheader(f"{profile_username}'s Recipes")
                for recipe in recipes:
                    # Display recipe details
                    if st.button(f"{recipe['title']}", key=f"recipe_button_{recipe['recipe_id']}"):
                        # Store the recipe_id or title in session state to pass it to the recipe details page
                        st.session_state.selected_recipe = recipe['recipe_id']  # Store recipe ID
                        st.session_state.page = 'recipe_details'  # Navigate to the recipe details page
                        st.rerun()

                    st.write(f"**Description:** {recipe['description']}")
                    st.write(f"**Submitted by:** {profile_username}")

                    # Display ratings as stars
                    recipe_rating = recipe.get("ratings", 0)  # Default to 0 if no rating exists
                    rating_display = display_rating(recipe_rating)
                    st.write(f"**Rating:** {rating_display}")
                    st.write("---")
            else:
                st.write("No recipes found.")

    else:
        st.error("User profile not found.")

# Update Profile
def update_user_profile(username, new_username, new_email, new_bio, new_dietary_id, new_profile_pic=None):
    db = connect_db()
    users_collection = db["users"]

    # Fetch existing user data
    existing_user = users_collection.find_one({"username": username})
    if not existing_user:
        return "User not found."

    # Prepare update fields
    update_fields = {}
    if existing_user.get("username") != new_username:
        update_fields["username"] = new_username
    if existing_user.get("email") != new_email:
        update_fields["email"] = new_email
    if existing_user.get("bio") != new_bio:
        update_fields["bio"] = new_bio
    if existing_user.get("dietary_id") != new_dietary_id:
        update_fields["dietary_id"] = new_dietary_id

    # Handle profile picture
    if new_profile_pic:
        profile_pic_path = save_profile_picture(username, new_profile_pic)
        if existing_user.get("profile_pic") != profile_pic_path:
            update_fields["profile_pic"] = profile_pic_path

    if not update_fields:
        return "No changes were made to the profile."

    # Perform the update
    update_result = users_collection.update_one(
        {"username": username},  # Match user by username
        {"$set": update_fields}  # Update fields
    )

    if update_result.modified_count > 0:
        # If username changed, return the new username
        return {"status": "success", "new_username": new_username}
    else:
        return "Failed to update the profile. Please try again."

def save_profile_picture(username, uploaded_file):
    """
    Save the uploaded profile picture to a directory or cloud storage.
    Returns the file path or URL for storing in the database.
    """
    # Save locally (for demonstration purposes)
    save_path = f"profile_pictures/{username}_{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path

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
def save_recipe(title, description, cook_time, servings, ingredients, instructions, user_id, image_file_name, dietary, cuisine):
    db = connect_db()
    recipes_collection = db["recipes"]  # Collection for storing recipes
        
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
            "ingredients": ingredients.split('\n'),
            "instructions": instructions.splitlines(),
            "user_id": user_id,
            "image_src": f"recipes/{uploaded_file.name}",  # Save relative path to the image
            "dietary": dietary,
            "cuisine": cuisine
        }
        
        result = recipes_collection.insert_one(new_recipe)
        return f"Recipe '{title}' saved successfully."

# Display Favorites
def show_favorites(username):
    db = connect_db()
    users_collection = db['users']
    favorites_collection = db['favorites']
    recipes_collection = db['recipes']

    # Find user by username
    user = users_collection.find_one({"username": username})
    
    if user:
        user_id = user["user_id"]
        
        # Query the favorites collection to find all favorite recipes for this user
        favorite_recipes = favorites_collection.find({"user_id": user_id})
        
        if favorite_recipes:
            for favorite in favorite_recipes:
                recipe_id = favorite['recipe_id']
                
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
                        favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe["recipe_id"]})
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
    favorites_collection = db['favorites']
    
    # Check if this user has already favorited the recipe
    favorite = favorites_collection.find_one({"user_id": user_id, "recipe_id": recipe_id})
    
    if favorite:
        # If found, remove it from the favorites collection
        favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
        st.success("Recipe removed from favorites!")
    else:
        # If not found, add it to the favorites collection
        favorites_collection.insert_one({"user_id": user_id, "recipe_id": recipe_id})
        st.success("Recipe added to favorites!")
    st.rerun()

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

    # Fetch the recipe
    recipe = recipes_collection.find_one({"recipe_id": recipe_id})
    recipe_info = recipe_info_collection.find_one({"recipeInfo_id": recipe_id})

    if recipe and recipe_info:
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

        # Upload recipe picture
        st.markdown("### Recipe Picture")
        uploaded_image = st.file_uploader(
            "Upload a new picture for the recipe", type=["png", "jpg", "jpeg"]
        )
        if uploaded_image:
            image_path = f"uploads/recipes/{uploaded_image.name}"
            with open(image_path, "wb") as f:
                f.write(uploaded_image.read())
        else:
            # Display the current image (if it exists)
            if recipe.get("image_src"):
                st.image(f"uploads/recipes/{recipe['image_src']}", caption="Current Recipe Picture", width=200)

        # Buttons for Update and Cancel
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Recipe"):
                # Prepare the update fields
                update_fields = {
                    "title": updated_title,
                    "description": updated_description,
                }
                
                if uploaded_image:
                    # If a new image is uploaded, update the image_src field
                    update_fields["image_src"] = uploaded_image.name
                
                # Update the recipes collection
                recipes_collection.update_one(
                    {"recipe_id": recipe_id},
                    {"$set": update_fields}
                )

                # Update the recipe_info collection
                recipe_info_collection.update_one(
                    {"recipeInfo_id": recipe_id},  # Match by integer ID
                    {"$set": {
                        "cook_timeserving": updated_cook_time,
                        "servings": updated_servings,
                        "ingredients": updated_ingredients,
                        "instructions": updated_instructions,
                    }}
                )
                st.success("Recipe updated successfully!")
                st.session_state.selected_recipe = None
                st.session_state.page = "user_profile"  # Navigate back to profile
                st.rerun()

        with col2:
            if st.button("Cancel"):
                st.session_state.selected_recipe = None
                st.session_state.page = "user_profile"  # Navigate back to profile
                st.rerun()
    else:
        st.error("Recipe not found!")

# Delete Recipe
def delete_recipe(recipe_id):
    db = connect_db()
    recipes_collection = db["recipes"]
    recipe_ratings_collection = db["recipe_ratings"]

    recipe_ratings_collection.delete_many({"recipe_id": recipe_id})
    recipes_collection.delete_one({"_id": recipe_id})
    st.success("Recipe deleted successfully!")