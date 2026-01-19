"""Configuration pour la connexion MongoDB"""
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "animals_db"
COLLECTION_NAME = "animals"
