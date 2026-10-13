# Project Charter — Leftover Chef

## 1. Project Identification
- **Project Name**: Leftover Chef — Smart Recipe Discovery and Ingredient Matching Platform
- **Version**: 1.0.0
- **Author & Lead Developer**: Developed by Anil Biradar

## 2. Problem Statement
Households frequently have small quantities of leftover vegetables, grains, dairy, and pantry staples (e.g., two potatoes, one onion, tomatoes, cooked rice, and a block of cheese) but lack a reliable tool to identify complete, step-by-step recipes that match those exact ingredients without requiring a large grocery run or relying on opaque, inaccurate match claims.

## 3. Project Objectives
1. Deliver a deterministic, transparent ingredient normalisation and recipe-matching engine that works 100% locally without requiring paid external AI APIs.
2. Preserve critical culinary and allergen distinctions (e.g., dairy milk vs coconut milk, wheat flour vs rice flour, bulb onion vs spring onion, peanuts vs tree nuts).
3. Provide accurate serving-size scaling and shopping-list generation that respects unit compatibility.
4. Enforce clear food-safety and allergen verification disclaimers.
5. Verify functionality through 60 automated test cases (TC-01 through TC-60).

## 4. Scope
- **In Scope**: Ingredient chip input, canonical alias resolution, recipe matching & ranking, serving scaling, personal pantry CRUD, shopping list CRUD with compatible-unit aggregation, favourites, user preferences, food-safety warnings, and automated backend/frontend test suites.
- **Out of Scope**: Medical dietary certification, automated physical spoilage detection, or unverified web scraping of copyrighted recipe websites.

---
**Developed by Anil Biradar**
