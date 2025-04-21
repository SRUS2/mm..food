from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source_url = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    bookmarked_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Recipe(title={self.title})"
    

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user")

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipe_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    image = Column(String, nullable=True)

    user = relationship("User", back_populates="bookmarks")

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    plan_data = Column(JSON, nullable=False)

    user = relationship("User", back_populates="meal_plans")