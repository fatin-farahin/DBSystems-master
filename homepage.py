# homepage.py

import streamlit as st
import pandas as pd
from bson import ObjectId
from db_connection import connect_db

def fetch_recipes(
    search_query: str = None,
    rating_filter: float = None,
    cuisine_filter: str = None,
    dietary_filter: str = None,
    cook_time_filter: int = None
) -> pd.DataFrame:
    db_collections = connect_db()  # Assuming this function connects to the database
    recipes_collection = db_collections["recipes"]

    pipeline = [
        {
            "$addFields": {
                "user_id": {
                    "$cond": {
                        "if": { "$eq": [{ "$type": "$user_id" }, "string"] },
                        "then": { "$toObjectId": "$user_id" },
                        "else": "$user_id"
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id", 
                "as": "user_info"
            }
        },
        {
            "$unwind": {
                "path": "$user_info",
                "preserveNullAndEmptyArrays": True  # Ensure capitalization of `True`
            }
        },
        {
            "$lookup": {
                "from": "recipe_info",
                "localField": "recipe_id",
                "foreignField": "_id",
                "as": "recipe_info"
            }
        },
        {
            "$unwind": {
                "path": "$recipe_info",
                "preserveNullAndEmptyArrays": True  # Ensure capitalization of `True`
            }
        },
        {
            "$lookup": {
                "from": "cuisines",
                "localField": "recipe_info.cuisine_id",
                "foreignField": "_id",
                "as": "cuisine_info"
            }
        },
        {
            "$unwind": {
                "path": "$cuisine_info",
                "preserveNullAndEmptyArrays": True  # Ensure capitalization of `True`
            }
        },
        {
            "$lookup": {
                "from": "dietary",
                "localField": "recipe_info.dietary_id",
                "foreignField": "_id",
                "as": "dietary_info"
            }
        },
        {
            "$unwind": {
                "path": "$dietary_info",
                "preserveNullAndEmptyArrays": True  # Ensure capitalization of `True`
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "title": { "$first": "$title" },
                "description": { "$first": "$description" },
                "user_id": { "$first": "$user_id" },
                "ratings": { "$first": "$ratings" },
                "cook_time": { "$first": "$recipe_info.cook_timeserving" },
                "servings": { "$first": "$recipe_info.servings" },
                "cuisine": { "$first": "$cuisine_info.name" },
                "dietary": { "$first": "$dietary_info.name" },
                "username": { "$first": "$user_info.username" }
            }
        }
    ]

    # Apply the filters if set
    if search_query:
        pipeline.insert(0, {"$match": {"$text": {"$search": search_query}}})
    if rating_filter:
        pipeline.append({"$match": {"ratings": {"$gte": rating_filter}}})
    if cuisine_filter and cuisine_filter != "All":
        pipeline.append({"$match": {"cuisine": cuisine_filter}})
    if dietary_filter and dietary_filter != "All":
        pipeline.append({"$match": {"dietary": dietary_filter}})
    if cook_time_filter:
        pipeline.append({"$match": {"cook_time": {"$lte": cook_time_filter}}})

    results = list(recipes_collection.aggregate(pipeline))
    recipes_df = pd.DataFrame(results)

    if not recipes_df.empty:
        recipes_df.rename(columns={"_id": "recipe_id"}, inplace=True)
        recipes_df.sort_values(by="title", inplace=True)  # Sort by title for consistent order

    return recipes_df

def display_rating(recipe_rating):
    """Display the rating with stars or 'No ratings yet' if no rating exists."""
    if pd.isna(recipe_rating) or recipe_rating == 0:
        return "No ratings yet"
    
    # Ensure the rating is within the 0-5 range
    recipe_rating = max(0, min(recipe_rating, 5))
    
    full_stars = "★" * int(recipe_rating)  # Unicode star for filled stars
    empty_stars = "☆" * (5 - int(recipe_rating))  # Unicode star for empty stars
    return full_stars + empty_stars

def add_to_favorites(user_id, recipe_id):
    db = connect_db()
    favorites_collection = db['favorites']
    
    # Add the favorite to the favorites collection
    favorites_collection.insert_one({"user_id": user_id, "recipe_id": recipe_id})
    st.success("Recipe added to favorites!")
    st.rerun()  # Refresh the page after the action

def remove_from_favorites(user_id, recipe_id):
    db = connect_db()
    favorites_collection = db['favorites']
    
    # Remove the favorite from the favorites collection
    favorites_collection.delete_one({"user_id": user_id, "recipe_id": recipe_id})
    st.success("Recipe removed from favorites!")
    st.rerun()  # Refresh the page after the action

def show_homepage():
    # Connect to the database
    db_collections = connect_db()

    # Access collections from the dictionary
    recipes_collection = db_collections["recipes"]
    users_collection = db_collections["users"]
    cuisines_collection = db_collections["cuisines"]
    dietary_collection = db_collections["dietary"]

    # Fetch the data from MongoDB collections
    users = pd.DataFrame(list(users_collection.find()))  # Fetch users collection
    users = users.to_dict('records')  # Convert the DataFrame to a list of dictionaries
    recipes = fetch_recipes(search_query=None)  # Get recipes without initial search
    cuisines = [cuisine['name'] for cuisine in cuisines_collection.find()]
    dietary = [diet['name'] for diet in dietary_collection.find()]

    # Remove duplicates from cuisines list
    cuisines = list(set(cuisines))  # Convert to set and back to list to remove duplicates
    cuisines.sort()  # Optional: Sort cuisines alphabetically

    # Ensure 'All' is the first option
    cuisines = ["All"] + cuisines
    dietary = ["All"] + dietary

    # Add "All" to the rating filter dropdown
    rating_options = ["All", 0, 1, 2, 3, 4, 5]

    # Replace missing or None values with default values (0 for ratings, servings, and cook_time)
    recipes['ratings'] = recipes['ratings'].fillna(0)  # Default to 0 if ratings are missing
    recipes['servings'] = recipes['servings'].fillna('Unknown')  # Default to 'Unknown' if servings are missing
    recipes['cook_time'] = recipes['cook_time'].fillna(0)  # Default to 0 if cook_time is missing

    # Create a dictionary mapping user_id (converted to string) to username
    user_dict = {str(user['user_id']): user['username'] for user in users}

    # Ensure 'user_id' in recipes is treated as string
    recipes['user_id'] = recipes['user_id'].apply(str)
 
    # Now map user_id in recipes to user_dict
    recipes['username'] = recipes['user_id'].apply(lambda user_id: user_dict.get(str(user_id), 'Unknown'))

    # Pass user_dict to recipe_details.py when navigating:
    st.session_state.user_dict = user_dict

    # Get the logged-in user's username from the session
    logged_in_username = st.session_state.get("username", None)

    if logged_in_username:
        # Fetch the logged-in user's data
        logged_in_user = users_collection.find_one({"username": logged_in_username})
        favorite_recipe_ids = logged_in_user.get('favorite_recipes', [])

    st.title("Welcome to Bitezy!")

    # Search bar
    search_query = st.text_input("Search for recipes by title, description, or username:")

    # First row for filters: Minimum Rating, Cuisine, Dietary Preferences
    col1, col2, col3 = st.columns([1, 1, 1])  # Adjust column widths

    with col1:
        rating_filter = st.selectbox("Minimum Rating", options=rating_options, index=0)  # Dropdown for rating

    with col2:
        cuisine_filter = st.selectbox("Cuisine", options=cuisines, index=0)  # Dropdown for cuisine

    with col3:
        dietary_filter = st.selectbox("Dietary Preferences", options=dietary, index=0)  # Dropdown for dietary preferences

    # Second row for the Cook Time slider
    col4 = st.columns([1])[0]  # Single column for the slider

    with col4:
        cook_time_filter = st.slider("Cook Time (mins)", min_value=0, max_value=120, step=5, value=120)  # Slider for cook time

    # Apply search filter
    if search_query:
        filtered_recipes = recipes[recipes['title'].str.contains(search_query, case=False, na=False) |
                                   recipes['description'].str.contains(search_query, case=False, na=False) |
                                   recipes['username'].str.contains(search_query, case=False, na=False)]
        
        # Display the count of matching recipes after applying filters
        st.write(f"Found {len(filtered_recipes)} matching recipes.")

    else:
        filtered_recipes = recipes

    # Apply the additional filters (rating, cuisine, dietary, cook time)
    if rating_filter != "All" and rating_filter is not None:
        filtered_recipes = filtered_recipes[filtered_recipes['ratings'] >= rating_filter]
    
    if cuisine_filter != "All":
        filtered_recipes = filtered_recipes[filtered_recipes['cuisine'].str.contains(cuisine_filter, case=False, na=False)]
    
    if dietary_filter != "All":
        filtered_recipes = filtered_recipes[filtered_recipes['dietary'].str.contains(dietary_filter, case=False, na=False)]

    filtered_recipes = filtered_recipes[filtered_recipes['cook_time'] <= cook_time_filter]

    st.title("Recipe List")

    # Display the recipes (whether filtered or all)
    if len(filtered_recipes) == 0:
        st.write("No recipes found matching your search term.")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(filtered_recipes.iterrows()):
            with cols[i % 2]:
                username = row['username']  # Directly get the username from the recipe DataFrame
                recipe_rating = row.get('ratings', 0)  # Default to 0 if no rating exists
                rating_display = display_rating(recipe_rating)

                # Create a button for each recipe title
                if st.button(row['title'], key=f"recipe_button_{row['recipe_id']}"):
                    # Store the recipe_id in session_state to pass it to the recipe_details page
                    st.session_state.selected_recipe = str(row['recipe_id'])
                    st.session_state.page = 'recipe_details'  # Navigate to the recipe details page
                    st.rerun()

                # Display recipe information
                st.write(f"**Description:** {row['description']}")
                # Create a clickable button for username
                if st.button(f"**Submitted by:** {username}", key=f"profile_button_{row['user_id']}_{row['recipe_id']}"):
                    # Navigate to the user profile
                    st.session_state.page = 'user_profile'  # Set the page to user_profile
                    st.session_state.viewing_username = username  # Track the user being viewed
                    st.rerun()
                st.write(f"**Rating:** {rating_display}")

                # Show Favorite/Unfavorite buttons if logged-in user is viewing their homepage
                if logged_in_username:
                    recipe_id = str(row['recipe_id'])  # Ensure recipe_id is a string
                    if recipe_id in favorite_recipe_ids:
                        if st.button(f"💔 Unfavorite", key=f"unfavorite_{row['recipe_id']}"):
                            remove_from_favorites(logged_in_user['_id'], row['recipe_id'])
                            # Update favorite_recipe_ids after removing the favorite
                            favorite_recipe_ids.remove(recipe_id)
                            st.session_state.favorite_recipe_ids = favorite_recipe_ids  # Update session state
                            st.rerun()
                    else:
                        if st.button(f"❤️ Favorite", key=f"favorite_{row['recipe_id']}"):
                            add_to_favorites(logged_in_user['_id'], row['recipe_id'])
                            # Update favorite_recipe_ids after adding the favorite
                            favorite_recipe_ids.append(recipe_id)
                            st.session_state.favorite_recipe_ids = favorite_recipe_ids  # Update session state
                            st.rerun()
                st.write("---")