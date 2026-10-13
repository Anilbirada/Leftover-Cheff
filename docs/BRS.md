# Business Requirements Specification (BRS) — Leftover Chef

## 1. Business Purpose
Reduce household food waste and simplify everyday meal preparation by matching available kitchen ingredients to verified, structured recipes.

## 2. Target Users
- **Home Cooks & Families**: Looking to turn leftover groceries into complete meals.
- **Students & Busy Professionals**: Seeking quick, low-ingredient recipes sorted by preparation time and missing items.
- **Dietary-Conscious Users**: Filtering recipes by vegetarian, vegan, gluten-free, dairy-free, or nut-free attributes while excluding specific disliked ingredients.

## 3. Key Business Requirements
- **BR-01 (Zero-Dependency Core Search)**: Users must be able to search and match recipes using local structured data without requiring third-party paid APIs.
- **BR-02 (Transparent Match Scoring)**: Every displayed match score must reflect the exact ratio of available required ingredients to total required ingredients.
- **BR-03 (Missing Ingredient Transparency)**: Users must clearly see which required ingredients they already have and which required ingredients they need to buy.
- **BR-04 (Pantry to Shopping Workflow)**: Users must be able to store common household staples in a pantry and export missing recipe ingredients to a shopping list.
- **BR-05 (Food Safety & Allergen Integrity)**: The platform must never claim that a digital best-before date proves food safety or that unverified recipes are medically allergy-safe.
- **BR-06 (Developer Attribution)**: Display "Developed by Anil Biradar" across the production footer, About/Credits section, and project documentation.

---
**Developed by Anil Biradar**
