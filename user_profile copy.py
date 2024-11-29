import streamlit as st
import base64
import os
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
                            st.session_state.selected_recipe = selected_recipe['recipe_id']  # Store the recipe ID in session state
                            st.session_state.page = 'edit_recipe'  # Navigate to edit_recipe page
                            st.rerun()
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