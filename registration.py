import streamlit as st
import hashlib
import re
from datetime import datetime
from db_connection import connect_db

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
    users_collection = db_collections["users"]  # Access the users collection from the returned dictionary

    # Initialize session state for error messages
    if 'errors' not in st.session_state:
        st.session_state.errors = {}

    username = st.text_input("Username", on_change=lambda: clear_error('username'))
    email = st.text_input("Email", on_change=lambda: clear_error('email'))
    password = st.text_input("Password", type="password", on_change=lambda: clear_error('password'))
    confirm_password = st.text_input("Confirm Password", type="password", on_change=lambda: clear_error('confirm_password'))

    # Function to clear specific error messages
    def clear_error(field):
        if field in st.session_state.errors:
            del st.session_state.errors[field]

    # Validation checks for username
    if username:
        if len(username) < 3:  # Check length first
            st.session_state.errors['username'] = "Username must be at least 3 characters long."
        else:
            # Check if the username is already taken in MongoDB
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                st.session_state.errors['username'] = "Username already exists. Please choose a different username."

    # Validation checks for email
    if email:
        if not is_valid_email(email):  # Check if email format is valid
            st.session_state.errors['email'] = "Invalid email format. Please enter a valid email (e.g., user@gmail.com)."
        else:
            # Check if the email is already taken in MongoDB
            existing_email = users_collection.find_one({"email": email})
            if existing_email:
                st.session_state.errors['email'] = "Email is already taken. Please use a different email."

    # Validation checks for password
    if password:
        if not is_valid_password(password):  # Validate password criteria
            st.session_state.errors['password'] = (
                "Password must be at least 6 characters long, "
                "contain at least one uppercase letter, one lowercase letter, and one digit."
            )

    # Validation check for confirm password
    if confirm_password:
        if confirm_password != password:
            st.session_state.errors['confirm_password'] = "Passwords do not match."

    # Display error messages below respective fields
    for field, error_msg in st.session_state.errors.items():
        st.error(error_msg)

    if st.button("Register", key="register_submit"):
        # Final checks before registration
        if not username or not email or not password or not confirm_password:
            st.error("Please fill in all fields.")
            return False  # Indicate registration was unsuccessful

        # If all checks pass, register the user
        hashed_password = hash_password(password)
        date_joined = datetime.now()

        # Store the new user in MongoDB
        new_user = {
            "username": username,
            "email": email,
            "password_hashed": hashed_password,
            "date_joined": date_joined
        }
        users_collection.insert_one(new_user)

        st.success("Registration successful! You can now log in.")
        
        # Set session state to redirect to the login page
        st.session_state.page = 'login'  # This will redirect to the login page
        st.rerun()  # Trigger a rerun to navigate to the login page

        return True  # Indicate successful registration

    return False  # Indicate registration was unsuccessful