import streamlit as st
import base64
import os
from db_connection import connect_db
from homepage import display_rating
from fetch_profile import update_user_profile, display_profile_picture
from fetch_recipe import show_edit_recipe, show_add_recipe, fetch_all_dietary_preferences, fetch_dietary_name, fetch_user_recipes
from favorites import show_favorites

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
            section = st.sidebar.selectbox("Choose an option", ["View Profile", "Update Profile", "Edit Recipes", "Add Recipes", "Favorites"])

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

                if new_profile_pic:
                    st.image(new_profile_pic, caption="Uploaded profile picture", width=300)

                if st.button("Save Changes"):
                    # Now pass each field individually to the update function
                    result = update_user_profile(
                        logged_in_username,  # Current username (for user identification)
                        new_username,        # New username
                        new_email,           # New email
                        new_bio,             # New bio
                        selected_dietary_id, # New dietary ID
                        new_profile_pic      # New profile pic (optional)
                    )

                    if isinstance(result, dict) and result.get("status") == "success":
                        st.success("Profile updated successfully!")
                        st.session_state["username"] = new_username  # Update logged-in username
                        logged_in_username = new_username
                        user = fetch_user_profile(logged_in_username)
                    else:
                        st.error(result)

            elif section == 'Edit Recipes':
                show_edit_recipe()

            elif section == 'Add Recipes':
                show_add_recipe()

            elif section == 'Favorites':
                st.subheader("Your Favorite Recipes")
                show_favorites(user.get('user_id'))

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