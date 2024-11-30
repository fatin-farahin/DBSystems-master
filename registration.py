# registration.py

import streamlit as st
import hashlib
import re
from datetime import datetime
from db_connection import connect_db
from fetch_profile import save_profile_picture

def hash_password(password):
    """Hashes a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    """Validates the email format using regex."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_valid_password(password):
    """Validates the password criteria."""
    if (len(password) < 6 or not re.search(r'[A-Z]', password) or 
        not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password)):
        return False
    return True

def show_registration():
    """Displays the registration page."""
    st.title("Register")

    # Connect to the database and get collections
    db_collections = connect_db()
    users_collection = db_collections["users"]
    dietary_collection = db_collections["dietary"]  # Access the dietary collection

    # Fetch the dietary options from MongoDB and convert the cursor to a list
    dietary_options = list(dietary_collection.find())  # Convert the cursor to a list

    # Build the list of dietary names and the mapping of names to dietary_ids
    dietary_names = [diet['name'] for diet in dietary_options]
    dietary_ids = {diet['name']: diet['dietary_id'] for diet in dietary_options}  # Correct mapping

    # Initialize session state for error messages
    if 'errors' not in st.session_state:
        st.session_state.errors = {}

    # Form fields
    username = st.text_input("Username", on_change=lambda: clear_error('username'))
    email = st.text_input("Email", on_change=lambda: clear_error('email'))
    password = st.text_input("Password", type="password", on_change=lambda: clear_error('password'))
    confirm_password = st.text_input("Confirm Password", type="password", on_change=lambda: clear_error('confirm_password'))
    bio = st.text_input("Bio", on_change=lambda: clear_error('bio'))  # Bio input

    # Profile Picture Upload
    profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])  # Image upload

    # Dietary Preference Dropdown
    dietary_name = st.selectbox("Select Dietary Preference", dietary_names)  # Dropdown of dietary names
    dietary_id = dietary_ids.get(dietary_name)  # Get dietary_id based on selected dietary_name

    # Function to clear specific error messages
    def clear_error(field):
        if field in st.session_state.errors:
            del st.session_state.errors[field]

    # Validation checks (similar to your previous code)
    if username:
        if len(username) < 3:  # Check length
            st.session_state.errors['username'] = "Username must be at least 3 characters long."
        else:
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                st.session_state.errors['username'] = "Username already exists."

    if email:
        if not is_valid_email(email):
            st.session_state.errors['email'] = "Invalid email format."
        else:
            existing_email = users_collection.find_one({"email": email})
            if existing_email:
                st.session_state.errors['email'] = "Email is already taken."

    if password:
        if not is_valid_password(password):
            st.session_state.errors['password'] = "Password must meet the criteria."

    if confirm_password and confirm_password != password:
        st.session_state.errors['confirm_password'] = "Passwords do not match."

    # Display error messages
    for field, error_msg in st.session_state.errors.items():
        st.error(error_msg)

    if st.button("Register", key="register_submit"):
        if not username or not email or not password or not confirm_password:
            st.error("Please fill in all fields.")
            return False

        # Handle profile_pic upload
        if profile_pic:
            profile_pic_url = save_profile_picture(username, profile_pic)  # Save the image file

        # Retrieve and increment user_id
        latest_user = users_collection.find().sort("user_id", -1).limit(1)
        latest_user_id = latest_user[0]["user_id"] if latest_user else 0
        user_id = latest_user_id + 1

        # Register the new user
        hashed_password = hash_password(password)
        date_joined = datetime.now()

        new_user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hashed": hashed_password,
            "bio": bio,
            "profile_pic": profile_pic_url if profile_pic else "",  # Store image URL or path
            "date_joined": date_joined,
            "dietary_id": dietary_id  # Save the dietary_id to MongoDB 
        }

        # Insert the new user into the users collection
        users_collection.insert_one(new_user)

        st.success("Registration successful!")

        # Redirect to login page (optional)
        st.session_state.page = 'login'
        st.rerun()

        return True

    return False