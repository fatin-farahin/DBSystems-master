import streamlit as st

# Import pages
from login import show_login  # Import the show_login function
from homepage import show_homepage  # Import the homepage display function
from registration import show_registration  # Import the registration function
from recipe_details import recipe_details  # Import recipe_details function
from user_profile import show_user_profile, show_edit_recipe_form  # Import user profile display function

def main():
    # Set up the session state for page navigation and user details
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False  # User is not logged in initially
        st.session_state.page = 'homepage'  # Default page is homepage
        st.session_state.user_id = None  # Initialize user_id
        st.session_state.username = None  # Initialize username

    # Sidebar for navigation
    st.sidebar.title("Navigation")

    # Add logo under the navigation title
    st.sidebar.image("uploads/logo.png", use_column_width=True)

    # Button for home page navigation
    if st.sidebar.button("Home", key="home_button"):
        st.session_state.page = 'homepage'  # Redirect to homepage
        st.rerun()  # Rerun the app to update the sidebar

    # Button for login/logout based on login status
    if st.session_state.logged_in:
        # Logout button is visible
        if st.sidebar.button("Logout", key="logout_button"):
            # Perform logout action
            st.session_state.logged_in = False  # Set login status to false
            st.session_state.username = None  # Clear username
            st.session_state.user_id = None  # Clear user_id on logout
            st.session_state.page = 'homepage'  # Redirect to homepage
            st.rerun()  # Rerun the app to update the sidebar
            
        if st.sidebar.button("Profile", key="profile_button"):
            st.session_state.page = 'user_profile'  # Navigate to user profile
            st.session_state.viewing_username = st.session_state.username  # Set viewing to logged-in user's profile
            st.rerun()  # Rerun to update the page

    else:
        # Login and Register buttons are visible
        if st.sidebar.button("Login", key="login_button"):
            st.session_state.page = 'login'  # Change to login page
        if st.sidebar.button("Register", key="register_button"):
            st.session_state.page = 'registration'  # Change to registration page

    # Navigation logic based on the page state
    if st.session_state.page == 'homepage':
        show_homepage()  # Display homepage content
    elif st.session_state.page == 'login':
        if show_login():  # Call the login function and check for successful login
            st.session_state.logged_in = True  # Set logged_in to True on successful login
            # Assume that the show_login function sets st.session_state.user_id
            st.session_state.page = 'homepage'  # Redirect to homepage
    elif st.session_state.page == 'registration':
        show_registration()  # Display registration page
    elif st.session_state.page == 'recipe_details':
        recipe_details()  # Call the recipe details function
    elif st.session_state.page == 'edit_recipe':
        if 'selected_recipe' in st.session_state and st.session_state.selected_recipe is not None:
            show_edit_recipe_form(st.session_state.selected_recipe)
        else:
            st.error("No recipe selected for editing.")
    elif st.session_state.page == 'user_profile':
        # Check if the user is logged in
        if st.session_state.logged_in:
            if st.session_state.viewing_username:
                show_user_profile(st.session_state.viewing_username)  # Show profile of the user being viewed
        else:
            # If not logged in, view the profile as a guest
            st.sidebar.text("Viewing profile as guest")
            if st.session_state.viewing_username:
                show_user_profile(st.session_state.viewing_username)  # Show profile as a guest


    # Optional: Consider adding a redirect after profile view
    if st.session_state.page == 'user_profile' and st.sidebar.button("Back to Home"):
        st.session_state.page = 'homepage'
        st.rerun()  # Rerun to go back to the homepage


if __name__ == "__main__":
    main()
