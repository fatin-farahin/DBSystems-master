# index_setup.py

from db_connection import connect_db

def setup_indexes():
    db = connect_db()

    # Users indexes
    db['users'].create_index("username", unique=True, name="username_unique_index", background=True)
    db['users'].create_index("email", unique=True, name="email_unique_index", background=True)
    db['users'].create_index("dietary_id", name="user_dietary_index", background=True)

    # Recipes indexes
    db['recipes'].create_index([("user_id", 1), ("ratings", -1)], name="user_ratings_compound_index", background=True)
    db['recipes'].create_index([("title", "text"), ("description", "text")], name="title_description_text_index", background=True)

    # Recipe info indexes
    db['recipe_info'].create_index("dietary_id", name="dietary_id_index", background=True)
    db['recipe_info'].create_index([("dietary_id", 1), ("cuisine_id", 1)], name="dietary_cuisine_compound_index", background=True)
    db['recipe_info'].create_index([("ingredients", "text"), ("instructions", "text")], name="ingredients_instructions_text_index", background=True)

    # Cuisines indexes
    db['cuisines'].create_index("cuisine_id", name="cuisine_id_index", background=True)
    db['cuisines'].create_index([("name", "text")], name="name_text_index", background=True)

    # Dietary indexes
    db['dietary'].create_index("dietary_id", name="dietary_id_index", background=True)
    db['dietary'].create_index([("name", "text"), ("description", "text")], name="dietary_text_index", background=True)

    # Favorites indexes
    db['favorites'].create_index([("user_id", 1), ("recipe_id", 1)], name="user_recipe_favorites_index", background=True)

    # Recipe ratings indexes
    db['recipe_ratings'].create_index([("recipe_id", 1), ("rating", -1)], name="recipe_rating_index", background=True)
    db['recipe_ratings'].create_index("user_id", name="user_rating_index", background=True)

    print("All indexes have been created successfully.")

if __name__ == "__main__":
    setup_indexes()