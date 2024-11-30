# fetch_profile.py

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
        # Save the profile picture and get the filename (not the full path)
        profile_pic_filename = save_profile_picture(new_profile_pic)
        if existing_user.get("profile_pic") != profile_pic_filename:
            update_fields["profile_pic"] = profile_pic_filename

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

def save_profile_picture(uploaded_file):
    # Create a directory for the user if it doesn't exist
    user_folder = "uploads/users"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Save the file with a unique filename (you could use the uploaded_file.name or a unique identifier)
    file_path = os.path.join(user_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Return only the filename, not the full path
    return uploaded_file.name

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