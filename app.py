# app.py
 
import streamlit as st
from db_connection import connect_db
from login import show_login
from homepage import show_homepage
from registration import show_registration
from recipe_details import recipe_details
from user_profile import show_user_profile
#from user_profile import show_user_profile, fetch_user_favorites, save_recipe, show_edit_recipe_form

def main():
    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state.page = 'homepage'  # Set the initial page to homepage
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'viewing_username' not in st.session_state:
        st.session_state.viewing_username = None  # For viewing user profiles

    # Sidebar for navigation
    st.sidebar.title("Navigation")

    # Button for login/logout based on login status
    if st.session_state.logged_in:
        if st.sidebar.button("Home"):
            st.session_state.page = 'homepage'

        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.logged_in_username = None
            st.session_state.page = 'homepage'
            st.rerun()

    else:
        if st.sidebar.button("Home"):
            st.session_state.page = 'homepage'
        if st.sidebar.button("Login", key="login_button"):
            st.session_state.page = 'login'
        if st.sidebar.button("Register", key="register_button"):
            st.session_state.page = 'registration'

    # Navigation logic based on the page state
    if st.session_state.page == 'homepage':
        show_homepage()
    elif st.session_state.page == 'login':
        show_login()
    elif st.session_state.page == 'registration':
        show_registration()
    elif st.session_state.page == 'recipe_details':
        recipe_details()
    elif st.session_state.page == 'user_profile' and st.session_state.viewing_username:
        show_user_profile(st.session_state.viewing_username)

if __name__ == "__main__":
    main()