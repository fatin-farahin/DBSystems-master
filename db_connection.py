# db_connection.py

from pymongo import MongoClient

def connect_db():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['inf2003_db']  # Database name
    
    # Collections to return
    collections = {
        "db": db,
        "recipes": db['recipes'],
        "users": db['users'],
        "recipe_info": db['recipe_info'],
        "recipe_ratings": db['recipe_ratings'],
        "cuisines": db['cuisines'],
        "dietary": db['dietary']
    }
    return collections