"""Relational database models for Leftover Chef."""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aliases: Mapped[List["IngredientAlias"]] = relationship(
        "IngredientAlias", back_populates="ingredient", cascade="all, delete-orphan"
    )


class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingredient_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(120), nullable=False)
    normalised_alias: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)

    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="aliases")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    preparation_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cooking_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    default_servings: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False, default="Easy")
    cuisine: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    instructions_json: Mapped[str] = mapped_column(Text, nullable=False)
    image_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    licence_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    recipe_ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )
    dietary_attributes: Mapped[List["RecipeDietaryAttribute"]] = relationship(
        "RecipeDietaryAttribute", back_populates="recipe", cascade="all, delete-orphan"
    )
    allergens: Mapped[List["RecipeAllergen"]] = relationship(
        "RecipeAllergen", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(32), nullable=False, default="required")
    preparation_note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient")


class RecipeDietaryAttribute(Base):
    __tablename__ = "recipe_dietary_attributes"
    __table_args__ = (
        UniqueConstraint("recipe_id", "attribute", name="uq_recipe_dietary_attr"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attribute: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="dietary_attributes")


class RecipeAllergen(Base):
    __tablename__ = "recipe_allergens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allergen: Mapped[str] = mapped_column(String(100), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(64), nullable=False, default="unverified")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="allergens")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    login_identifier: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    secure_authentication_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    dietary_preferences_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    disliked_ingredients_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    preferred_cuisine: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    typical_serving_size: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_cooking_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class UserPantryItem(Base):
    __tablename__ = "user_pantry_items"
    __table_args__ = (
        UniqueConstraint("user_id", "ingredient_id", name="uq_user_pantry_ingredient"),
        Index("ix_pantry_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit: Mapped[str] = mapped_column(String(64), nullable=False, default="piece")
    purchase_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    best_before_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    storage_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    ingredient: Mapped["Ingredient"] = relationship("Ingredient")


class UserFavourite(Base):
    __tablename__ = "user_favourites"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_favourite_recipe"),
        Index("ix_favourites_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recipe_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    recipe: Mapped["Recipe"] = relationship("Recipe")


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="My Shopping List")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    items: Mapped[List["ShoppingListItem"]] = relationship(
        "ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan"
    )


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shopping_list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shopping_lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("ingredients.id", ondelete="SET NULL"), nullable=True
    )
    ingredient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(64), nullable=False, default="piece")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_recipe_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )

    shopping_list: Mapped["ShoppingList"] = relationship("ShoppingList", back_populates="items")
    ingredient: Mapped[Optional["Ingredient"]] = relationship("Ingredient")
    related_recipe: Mapped[Optional["Recipe"]] = relationship("Recipe")
