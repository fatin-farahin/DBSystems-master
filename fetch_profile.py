# user_profile.py

import streamlit as st
import base64
import os
from db_connection import connect_db
from homepage import display_rating, remove_from_favorites

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