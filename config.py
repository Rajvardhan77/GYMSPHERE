"""Configuration settings for the GymSphere Flask application."""
import os


class Config:
    """Base configuration."""

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "gym.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False





