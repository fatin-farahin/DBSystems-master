# login.py

import streamlit as st
import hashlib
from db_connection import connect_db

# Function to hash password
def hash_password(password):
    """Hashes a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# Function to check password hash
def check_password_hash(stored_password, provided_password):
    """Checks if the provided password matches the stored hashed password."""
    return stored_password == hash_password(provided_password)

# Function to handle login
def show_login():
    """Displays the login page."""
    st.title("Login")

    # Input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="login_submit"):
        # Check if both fields are filled
        if not username or not password:
            st.error("Please fill in all fields.")
            return False  # Indicate login was unsuccessful

        # Connect to the database and get collections
        db_collections = connect_db()
        users_collection = db_collections["users"]  # Access the users collection from the returned dictionary

        # Query the MongoDB collection 'users' to find the user by username
        user = users_collection.find_one({"username": username})

        if user:
            # Check password hash
            if check_password_hash(user['password_hashed'], password):  # Assuming password is stored as 'password_hashed'
                st.session_state["username"] = username  # Store username in session state
                
                # Fetch user_id from the correct field in the user document
                user_id = user.get("user_id", str(user["_id"]))  # Use custom user_id if available, otherwise fallback to _id
                st.session_state["user_id"] = user_id  # Store user_id in session state (convert to string if necessary)
                
                st.session_state['logged_in'] = True  # Track login status
                st.success("Login successful! Redirecting to the homepage...")
                st.session_state.page = 'homepage'  # Redirect to homepage
                return True  # Indicate successful login
            else:
                st.error("Wrong password. Please try again.")
        else:
            st.error("User does not exist. Please register.")

    # Navigate to the registration page directly
    if st.button("Don't have an account? Register here.", key="register_button_login"):
        st.session_state.page = 'registration'  # Redirect to the registration page

    return False  # Indicate login was unsuccessful