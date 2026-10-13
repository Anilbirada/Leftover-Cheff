"""
Automated Verification Suite for Leftover Chef Backend (TC-01 through TC-52).

Uses an isolated SQLite test database seeded with the official `data/seed/catalogue.json`.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.services.ai_assistant import generate_recipe_match_explanation
from app.services.matcher import search_recipes_by_ingredients
from app.services.scaler import combine_compatible_quantities
from app.services.seed_service import seed_database_from_file, validate_catalogue_payload


TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE, future=True)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    seed_database_from_file(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================
# INGREDIENT INPUT AND NORMALISATION (TC-01 to TC-10)
# ============================================================

def test_tc01_submit_one_valid_ingredient(client: TestClient):
    """TC-01: Submit one valid ingredient."""
    res = client.post("/api/v1/recipes/search-by-ingredients", json={"ingredients": ["potato"]})
    assert res.status_code == 200
    data = res.json()
    assert len(data["normalised_user_ingredients"]) == 1
    assert data["normalised_user_ingredients"][0]["canonical_name"] == "potato"
    assert data["normalised_user_ingredients"][0]["is_recognised"] is True
    assert "ing_potato" in data["recognised_ingredient_ids"]


def test_tc02_submit_multiple_comma_separated_ingredients(client: TestClient):
    """TC-02: Submit multiple comma-separated ingredients."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato, onion, tomato, rice"]},
    )
    assert res.status_code == 200
    data = res.json()
    canon_names = [i["canonical_name"] for i in data["normalised_user_ingredients"]]
    assert canon_names == ["potato", "onion", "tomato", "rice"]


def test_tc03_handle_empty_input(client: TestClient):
    """TC-03: Handle empty input gracefully."""
    res = client.post("/api/v1/recipes/search-by-ingredients", json={"ingredients": ["   ", ""]})
    assert res.status_code == 200
    data = res.json()
    assert data["normalised_user_ingredients"] == []
    assert data["matched_recipes"] == []
    assert data["no_match_guidance"] is not None


def test_tc04_remove_repeated_whitespace(client: TestClient):
    """TC-04: Remove repeated whitespace and punctuation."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["   spring    onions  ", "  cooking   oil! "]},
    )
    assert res.status_code == 200
    data = res.json()
    names = [i["canonical_name"] for i in data["normalised_user_ingredients"]]
    assert names == ["spring onion", "cooking oil"]


def test_tc05_handle_repeated_ingredients(client: TestClient):
    """TC-05: Deduplicate repeated ingredients including aliases and plurals."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "potatoes", "aloo", "POTATO"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["normalised_user_ingredients"]) == 1
    assert data["recognised_ingredient_ids"] == ["ing_potato"]


def test_tc06_handle_case_differences(client: TestClient):
    """TC-06: Handle case differences."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["ToMaTo", "ONION", "rIcE"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert set(data["recognised_ingredient_ids"]) == {"ing_tomato", "ing_onion", "ing_rice"}


def test_tc07_resolve_approved_ingredient_alias(client: TestClient):
    """TC-07: Resolve approved ingredient aliases (e.g., scallion -> spring onion, garbanzo beans -> chickpeas)."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["scallions", "garbanzo beans", "jeera"]},
    )
    assert res.status_code == 200
    data = res.json()
    resolved_ids = set(data["recognised_ingredient_ids"])
    assert resolved_ids == {"ing_spring_onion", "ing_chickpeas", "ing_cumin_seeds"}


def test_tc08_do_not_incorrectly_merge_distinct_ingredients(client: TestClient):
    """TC-08: Preserve distinctions between milk/coconut milk, butter/margarine, wheat/rice flour, onion/spring onion, chilli/chilli powder, peanuts/tree nuts."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={
            "ingredients": [
                "milk",
                "coconut milk",
                "butter",
                "margarine",
                "wheat flour",
                "rice flour",
                "onion",
                "spring onion",
                "fresh chilli",
                "chilli powder",
                "peanuts",
                "tree nuts",
            ]
        },
    )
    assert res.status_code == 200
    data = res.json()
    ids = set(data["recognised_ingredient_ids"])
    assert len(ids) == 12
    assert "ing_milk" in ids and "ing_coconut_milk" in ids
    assert "ing_butter" in ids and "ing_margarine" in ids
    assert "ing_wheat_flour" in ids and "ing_rice_flour" in ids
    assert "ing_onion" in ids and "ing_spring_onion" in ids
    assert "ing_fresh_chilli" in ids and "ing_chilli_powder" in ids
    assert "ing_peanuts" in ids and "ing_tree_nuts" in ids


def test_tc09_reject_oversized_input_appropriately(client: TestClient):
    """TC-09: Reject oversized ingredient input payload."""
    oversized = ["potato" * 300]
    res = client.post("/api/v1/recipes/search-by-ingredients", json={"ingredients": oversized})
    assert res.status_code == 422


def test_tc10_handle_unknown_ingredient_gracefully(client: TestClient):
    """TC-10: Handle an unknown ingredient gracefully while still matching valid ones."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["dragonfruit_xyz", "potato", "onion"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "dragonfruit_xyz" in data["unrecognised_inputs"]
    assert set(data["recognised_ingredient_ids"]) == {"ing_potato", "ing_onion"}
    assert len(data["matched_recipes"]) > 0


# ============================================================
# RECIPE MATCHING (TC-11 to TC-20)
# ============================================================

def test_tc11_find_recipe_when_all_required_ingredients_available(client: TestClient):
    """TC-11: Find a recipe with 100% score when all required ingredients are available."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["rice", "tomato", "onion", "cooking oil", "salt"]},
    )
    assert res.status_code == 200
    matches = res.json()["matched_recipes"]
    top = next(m for m in matches if m["recipe"]["id"] == "rec_spiced_tomato_onion_rice")
    assert top["core_coverage_score"] == 100.0
    assert top["missing_required_count"] == 0
    assert top["matched_required_count"] == 5


def test_tc12_identify_recipe_with_some_missing_ingredients(client: TestClient):
    """TC-12: Identify a recipe with partial required ingredients and list missing ones."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "tomato", "onion"]},
    )
    assert res.status_code == 200
    matches = res.json()["matched_recipes"]
    curry = next(m for m in matches if m["recipe"]["id"] == "rec_potato_tomato_curry")
    # Potato Tomato Curry has 6 required: potato, tomato, onion, cooking oil, salt, turmeric powder
    assert curry["matched_required_count"] == 3
    assert curry["missing_required_count"] == 3
    assert curry["core_coverage_score"] == 50.0
    missing_names = {i["canonical_name"] for i in curry["missing_required_ingredients"]}
    assert missing_names == {"cooking oil", "salt", "turmeric powder"}


def test_tc13_exclude_optional_ingredients_from_required_coverage(client: TestClient):
    """TC-13: Optional ingredients are excluded from the required coverage denominator as documented."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "tomato", "onion", "cooking oil", "salt", "turmeric powder"]},
    )
    assert res.status_code == 200
    matches = res.json()["matched_recipes"]
    curry = next(m for m in matches if m["recipe"]["id"] == "rec_potato_tomato_curry")
    assert curry["core_coverage_score"] == 100.0
    assert curry["missing_required_count"] == 0
    assert curry["missing_optional_count"] == 3


def test_tc14_return_no_match_guidance_for_unsuitable_searches(client: TestClient):
    """TC-14: Return helpful no-match guidance when no recipe matches."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["unknown_herb_123"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["matched_recipes"] == []
    assert data["no_match_guidance"] is not None
    assert "unknown_herb_123" in data["no_match_guidance"]


def test_tc15_rank_recipes_using_documented_ranking_rules(client: TestClient):
    """TC-15: Rank recipes deterministically by highest required coverage, then matched count, then fewest missing."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "onion", "tomato", "rice", "cheese", "cooking oil", "salt"]},
    )
    assert res.status_code == 200
    matches = res.json()["matched_recipes"]
    scores = [m["core_coverage_score"] for m in matches]
    assert scores == sorted(scores, reverse=True)
    # Cheesy Potato, Onion & Tomato Skillet (6/6), Spiced Tomato & Onion Rice (5/5), and Quick Cheesy Tomato & Potato Rice Skillet (7/7) should all be 100%
    top_ids = [m["recipe"]["id"] for m in matches if m["core_coverage_score"] == 100.0]
    assert "rec_cheesy_tomato_rice_bake" in top_ids
    # 7 matched required ingredients ranks ahead of 6 matched required ingredients at 100% coverage
    assert matches[0]["recipe"]["id"] == "rec_cheesy_tomato_rice_bake"


def test_tc16_confirm_matching_scores_use_actual_ingredient_records(client: TestClient):
    """TC-16: Confirm matching score equals round((matched_required / total_required) * 100, 1)."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "onion", "tomato", "cheese"]},
    )
    assert res.status_code == 200
    for m in res.json()["matched_recipes"]:
        expected = round((m["matched_required_count"] / m["total_required_count"]) * 100.0, 1)
        assert m["core_coverage_score"] == expected


def test_tc17_do_not_claim_ingredient_is_available_if_missing(client: TestClient):
    """TC-17: Never mark a missing ingredient as available."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["pasta", "garlic"]},
    )
    assert res.status_code == 200
    pasta_match = next(
        m for m in res.json()["matched_recipes"] if m["recipe"]["id"] == "rec_garlic_butter_pasta"
    )
    avail_ids = {i["ingredient_id"] for i in pasta_match["matched_required_ingredients"]}
    missing_ids = {i["ingredient_id"] for i in pasta_match["missing_required_ingredients"]}
    assert avail_ids == {"ing_pasta", "ing_garlic"}
    assert "ing_butter" in missing_ids
    assert "ing_cheese" in missing_ids
    assert avail_ids.isdisjoint(missing_ids)


def test_tc18_confirm_dietary_filters_work_with_supported_metadata(client: TestClient):
    """TC-18: Dietary filters return only recipes carrying all requested dietary attributes."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={
            "ingredients": ["potato", "onion", "tomato", "cheese", "cooking oil", "salt"],
            "dietary_filters": ["vegan"],
        },
    )
    assert res.status_code == 200
    matches = res.json()["matched_recipes"]
    assert len(matches) > 0
    for m in matches:
        assert "vegan" in m["recipe"]["dietary_attributes"]
        assert m["recipe"]["id"] != "rec_cheesy_potato_onion_skillet"


def test_tc19_confirm_excluded_ingredients_are_handled_correctly(client: TestClient):
    """TC-19: Excluded ingredients (including aliases) remove any recipe containing that ingredient."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={
            "ingredients": ["rice", "onion", "tomato", "cooking oil", "salt", "peanuts"],
            "excluded_ingredients": ["groundnuts"],  # Alias for peanuts
        },
    )
    assert res.status_code == 200
    ids = [m["recipe"]["id"] for m in res.json()["matched_recipes"]]
    assert "rec_peanut_garlic_rice_bowl" not in ids
    assert "rec_spiced_tomato_onion_rice" in ids


def test_tc20_confirm_result_sorting_behaves_consistently(client: TestClient):
    """TC-20: Confirm sorting options (shortest_time, fewest_missing, alphabetical) work consistently."""
    res_time = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["onion", "tomato", "egg", "potato"], "sort_by": "shortest_time"},
    )
    times = [m["recipe"]["total_minutes"] for m in res_time.json()["matched_recipes"]]
    assert times == sorted(times)

    res_alpha = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["onion", "tomato", "egg", "potato"], "sort_by": "alphabetical"},
    )
    names = [m["recipe"]["name"].lower() for m in res_alpha.json()["matched_recipes"]]
    assert names == sorted(names)


# ============================================================
# RECIPE DETAILS AND QUANTITIES (TC-21 to TC-28)
# ============================================================

def test_tc21_retrieve_valid_recipe(client: TestClient):
    """TC-21: Retrieve a valid recipe by ID."""
    res = client.get("/api/v1/recipes/rec_potato_tomato_curry")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "rec_potato_tomato_curry"
    assert data["default_servings"] == 2
    assert len(data["ingredients"]) == 9


def test_tc22_handle_recipe_that_does_not_exist(client: TestClient):
    """TC-22: Return 404 for a non-existent recipe ID."""
    res = client.get("/api/v1/recipes/rec_nonexistent_dish")
    assert res.status_code == 404


def test_tc23_display_ingredient_quantities_and_units_correctly(client: TestClient):
    """TC-23: Display structured quantities and units accurately."""
    res = client.get("/api/v1/recipes/rec_potato_tomato_curry")
    ings = {i["ingredient_id"]: i for i in res.json()["ingredients"]}
    assert ings["ing_potato"]["quantity"] == 2.0
    assert ings["ing_potato"]["unit"] == "piece"
    assert ings["ing_potato"]["display_quantity"] == "2 piece"


def test_tc24_scale_ingredients_for_different_serving_count(client: TestClient):
    """TC-24: Scale recipe quantities accurately (e.g., 2 potatoes for 2 servings -> 4 potatoes for 4 servings)."""
    res = client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": 4})
    assert res.status_code == 200
    data = res.json()
    assert data["original_servings"] == 2
    assert data["requested_servings"] == 4
    ings = {i["ingredient_id"]: i for i in data["ingredients"]}
    assert ings["ing_potato"]["original_quantity"] == 2.0
    assert ings["ing_potato"]["adjusted_quantity"] == 4.0
    assert ings["ing_potato"]["display_quantity"] == "4 piece"


def test_tc25_preserve_qualitative_quantities_such_as_to_taste(client: TestClient):
    """TC-25: Preserve qualitative quantities ('to taste') without inventing numbers."""
    res = client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": 6})
    assert res.status_code == 200
    ings = {i["ingredient_id"]: i for i in res.json()["ingredients"]}
    assert ings["ing_salt"]["original_quantity"] is None
    assert ings["ing_salt"]["adjusted_quantity"] is None
    assert ings["ing_salt"]["display_quantity"] == "to taste"


def test_tc26_do_not_apply_unsupported_mass_to_volume_conversions():
    """TC-26: Reject mass-to-volume conversions (e.g. g to ml or cup) without density data."""
    with pytest.raises(ValueError, match="Cannot safely convert"):
        combine_compatible_quantities(100, "g", 50, "ml")
    with pytest.raises(ValueError, match="Cannot safely convert"):
        combine_compatible_quantities(100, "g", 1, "cup")


def test_tc27_preserve_original_recipe_data_after_serving_adjustments(client: TestClient):
    """TC-27: Scaling servings does not overwrite the stored recipe's default quantities."""
    client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": 10})
    res = client.get("/api/v1/recipes/rec_potato_tomato_curry")
    assert res.status_code == 200
    data = res.json()
    assert data["default_servings"] == 2
    ings = {i["ingredient_id"]: i for i in data["ingredients"]}
    assert ings["ing_potato"]["quantity"] == 2.0


def test_tc28_display_cooking_instructions_in_correct_order(client: TestClient):
    """TC-28: Cooking instructions are returned in their exact step-by-step sequence."""
    res = client.get("/api/v1/recipes/rec_potato_tomato_curry")
    steps = res.json()["instructions"]
    assert len(steps) == 6
    assert steps[0].startswith("Peel and cut the potatoes")
    assert steps[-1].startswith("Mash two or three potato cubes")


# ============================================================
# PANTRY AND FAVOURITES (TC-29 to TC-34)
# ============================================================

def test_tc29_add_pantry_item(client: TestClient):
    """TC-29: Add a pantry item."""
    res = client.post(
        "/api/v1/pantry/items",
        json={
            "ingredient_name": "potatoes",
            "quantity": 4,
            "unit": "piece",
            "best_before_date": "2026-10-20",
            "storage_note": "Cool dark basket",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["canonical_name"] == "potato"
    assert data["quantity"] == 4.0
    assert "do not prove food safety" in data["food_safety_reminder"]


def test_tc30_update_pantry_quantity(client: TestClient):
    """TC-30: Update a pantry item's quantity."""
    add_res = client.post(
        "/api/v1/pantry/items",
        json={"ingredient_name": "onion", "quantity": 2, "unit": "piece"},
    )
    item_id = add_res.json()["id"]
    patch_res = client.patch(f"/api/v1/pantry/items/{item_id}", json={"quantity": 5})
    assert patch_res.status_code == 200
    assert patch_res.json()["quantity"] == 5.0


def test_tc31_delete_pantry_item(client: TestClient):
    """TC-31: Delete a pantry item."""
    add_res = client.post(
        "/api/v1/pantry/items",
        json={"ingredient_name": "tomato", "quantity": 3, "unit": "piece"},
    )
    item_id = add_res.json()["id"]
    del_res = client.delete(f"/api/v1/pantry/items/{item_id}")
    assert del_res.status_code == 204
    list_res = client.get("/api/v1/pantry/items")
    assert all(i["id"] != item_id for i in list_res.json())


def test_tc32_save_favourite_recipe(client: TestClient):
    """TC-32: Save a favourite recipe."""
    res = client.post("/api/v1/favourites/rec_potato_tomato_curry")
    assert res.status_code == 201
    assert res.json()["recipe_id"] == "rec_potato_tomato_curry"
    favs = client.get("/api/v1/favourites").json()
    assert len(favs) == 1


def test_tc33_remove_favourite_recipe(client: TestClient):
    """TC-33: Remove a favourite recipe."""
    client.post("/api/v1/favourites/rec_potato_tomato_curry")
    del_res = client.delete("/api/v1/favourites/rec_potato_tomato_curry")
    assert del_res.status_code == 204
    assert client.get("/api/v1/favourites").json() == []


def test_tc34_prevent_unauthorised_access_to_private_user_data(client: TestClient):
    """TC-34: Prevent one user from accessing or modifying another user's pantry/favourites/shopping list."""
    # User A adds a pantry item
    res_a = client.post(
        "/api/v1/pantry/items",
        headers={"X-User-ID": "chef_alice"},
        json={"ingredient_name": "cheese", "quantity": 200, "unit": "g"},
    )
    assert res_a.status_code == 201
    alice_item_id = res_a.json()["id"]

    # User B cannot see User A's pantry item or delete it
    res_b_list = client.get("/api/v1/pantry/items", headers={"X-User-ID": "chef_bob"})
    assert res_b_list.json() == []
    res_b_del = client.delete(f"/api/v1/pantry/items/{alice_item_id}", headers={"X-User-ID": "chef_bob"})
    assert res_b_del.status_code == 404

    # Protected namespace without valid token is rejected with 403
    unauth = client.get("/api/v1/pantry/items", headers={"X-User-ID": "private_user1"})
    assert unauth.status_code == 403


# ============================================================
# SHOPPING LIST (TC-35 to TC-39)
# ============================================================

def test_tc35_add_missing_ingredient_to_shopping_list(client: TestClient):
    """TC-35: Add a missing ingredient linked to a recipe to the shopping list."""
    res = client.post(
        "/api/v1/shopping-list/items",
        json={
            "ingredient_name": "turmeric powder",
            "quantity": 0.5,
            "unit": "teaspoon",
            "related_recipe_id": "rec_potato_tomato_curry",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["ingredient_name"] == "turmeric powder"
    assert data["related_recipe_id"] == "rec_potato_tomato_curry"


def test_tc36_mark_shopping_item_as_purchased(client: TestClient):
    """TC-36: Mark a shopping list item as purchased/completed."""
    add_res = client.post(
        "/api/v1/shopping-list/items",
        json={"ingredient_name": "cheese", "quantity": 60, "unit": "g"},
    )
    item_id = add_res.json()["id"]
    patch_res = client.patch(f"/api/v1/shopping-list/items/{item_id}", json={"completed": True})
    assert patch_res.status_code == 200
    assert patch_res.json()["completed"] is True


def test_tc37_remove_shopping_list_item(client: TestClient):
    """TC-37: Remove an item from the shopping list."""
    add_res = client.post(
        "/api/v1/shopping-list/items",
        json={"ingredient_name": "butter", "quantity": 30, "unit": "g"},
    )
    item_id = add_res.json()["id"]
    del_res = client.delete(f"/api/v1/shopping-list/items/{item_id}")
    assert del_res.status_code == 204
    sl = client.get("/api/v1/shopping-list").json()
    assert all(i["id"] != item_id for i in sl["items"])


def test_tc38_handle_duplicate_shopping_ingredients_appropriately(client: TestClient):
    """TC-38: Merge duplicate shopping items when units are compatible; keep separate when incompatible."""
    # Compatible units: 60 g + 40 g = 100 g
    client.post("/api/v1/shopping-list/items", json={"ingredient_name": "cheese", "quantity": 60, "unit": "g"})
    client.post("/api/v1/shopping-list/items", json={"ingredient_name": "cheddar", "quantity": 40, "unit": "g"})

    # Incompatible unit: 1 cup cheese kept separate from g
    client.post("/api/v1/shopping-list/items", json={"ingredient_name": "cheese", "quantity": 1, "unit": "cup"})

    items = client.get("/api/v1/shopping-list").json()["items"]
    cheese_items = [i for i in items if i["ingredient_name"] == "cheese"]
    assert len(cheese_items) == 2
    by_unit = {i["unit"]: i["quantity"] for i in cheese_items}
    assert by_unit["g"] == 100.0
    assert by_unit["cup"] == 1.0


def test_tc39_preserve_shopping_quantities_and_units_correctly(client: TestClient):
    """TC-39: Preserve quantities and units in shopping list display."""
    res = client.post(
        "/api/v1/shopping-list/items",
        json={"ingredient_name": "coconut milk", "quantity": 200, "unit": "ml"},
    )
    assert res.status_code == 201
    assert res.json()["display_quantity"] == "200 ml"


# ============================================================
# FOOD SAFETY AND CONTENT (TC-40 to TC-43)
# ============================================================

def test_tc40_do_not_claim_unverified_allergen_safety(client: TestClient):
    """TC-40: Never claim a recipe is medically allergy-safe without caveats."""
    res = client.get("/api/v1/recipes/rec_potato_tomato_curry")
    notice = res.json()["allergen_verification_notice"]
    assert "cross-contamination" in notice.lower()


def test_tc41_handle_recipes_with_unknown_allergen_information(client: TestClient):
    """TC-41: Display 'Allergen information not verified' when a recipe has unverified allergen status."""
    res = client.get("/api/v1/recipes/rec_spring_onion_soy_fried_rice")
    data = res.json()
    assert "Allergen information not verified" in data["allergen_verification_notice"]


def test_tc42_ensure_unverified_ai_suggestions_are_labelled_appropriately(client: TestClient):
    """TC-42: Optional AI/assistant explanations are explicitly labelled as unverified suggestions."""
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": ["potato", "onion", "tomato"], "include_ai_explanation": True},
    )
    assert res.status_code == 200
    first_ai = res.json()["matched_recipes"][0]["ai_suggestion"]
    assert first_ai is not None
    assert first_ai["is_ai_generated"] is True
    assert first_ai["verification_status"] == "unverified_suggestion"
    assert "Suggestion only" in first_ai["safety_disclaimer"]


def test_tc43_do_not_claim_expiry_date_comparison_proves_food_safety(client: TestClient):
    """TC-43: Pantry items with future best-before dates explicitly warn that dates do not prove food safety."""
    res = client.post(
        "/api/v1/pantry/items",
        json={
            "ingredient_name": "milk",
            "quantity": 500,
            "unit": "ml",
            "best_before_date": "2099-12-31",
        },
    )
    assert res.status_code == 201
    reminder = res.json()["food_safety_reminder"].lower()
    assert "do not prove food safety" in reminder


# ============================================================
# BACKEND AND SECURITY (TC-44 to TC-52)
# ============================================================

def test_tc44_validate_api_input(client: TestClient):
    """TC-44: Validate API input types and required fields."""
    res = client.post("/api/v1/pantry/items", json={"ingredient_name": "", "quantity": -5})
    assert res.status_code == 422


def test_tc45_return_controlled_errors_for_invalid_requests(client: TestClient):
    """TC-45: Return structured JSON error responses without stack traces."""
    res = client.get("/api/v1/recipes/non_existent_id")
    assert res.status_code == 404
    assert "detail" in res.json()


def test_tc46_prevent_sql_injection(client: TestClient):
    """TC-46: SQL injection payloads in search queries or ingredient inputs are treated as harmless strings."""
    sqli_payload = "potato'; DROP TABLE recipes; --"
    res = client.post(
        "/api/v1/recipes/search-by-ingredients",
        json={"ingredients": [sqli_payload, "potato"]},
    )
    assert res.status_code == 200
    # Verify recipes table is completely intact
    health = client.get("/api/v1/health").json()
    assert health["catalogue_recipes_count"] == 12


def test_tc47_prevent_unsafe_html_rendering(client: TestClient):
    """TC-47: Sanitize HTML/XSS payloads in user-supplied profile and storage note fields."""
    res = client.put(
        "/api/v1/profile",
        json={"display_name": "<script>alert('xss')</script>Chef"},
    )
    assert res.status_code == 200
    name = res.json()["display_name"]
    assert "<script>" not in name
    assert "&lt;script&gt;" in name


def test_tc48_protect_secrets_in_responses_and_logs(client: TestClient):
    """TC-48: Health and API endpoints never expose secret_key or API keys."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body_text = res.text.lower()
    assert "secret_key" not in body_text
    assert "ai_provider_api_key" not in body_text
    assert res.json()["developer_credit"] == "Developed by Anil Biradar"


def test_tc49_enforce_user_specific_access_controls(client: TestClient):
    """TC-49: Reject invalid X-User-ID header formats and enforce user isolation."""
    bad_header = client.get("/api/v1/pantry/items", headers={"X-User-ID": "../admin/secret"})
    assert bad_header.status_code == 400


def test_tc50_handle_unavailable_external_provider_gracefully(db_session):
    """TC-50: Handle an unavailable external AI provider gracefully with deterministic fallback."""
    outcome = search_recipes_by_ingredients(db_session, ["potato", "onion", "tomato"])
    suggestion = generate_recipe_match_explanation(outcome.matched_recipes[0], simulate_provider_failure=True)
    assert suggestion.provider_status == "fallback_deterministic_provider_unavailable"
    assert len(suggestion.explanation) > 10


def test_tc51_prevent_invalid_serving_counts(client: TestClient):
    """TC-51: Reject zero, negative, or excessive serving counts."""
    res_zero = client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": 0})
    assert res_zero.status_code == 422
    res_neg = client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": -2})
    assert res_neg.status_code == 422
    res_huge = client.post("/api/v1/recipes/rec_potato_tomato_curry/servings", json={"servings": 500})
    assert res_huge.status_code == 422


def test_tc52_ensure_shopping_list_and_pantry_use_validated_data(client: TestClient):
    """TC-52: Reject unknown catalogue ingredients in pantry and validate catalogue seed format."""
    bad_pantry = client.post(
        "/api/v1/pantry/items",
        json={"ingredient_name": "unobtainium_mineral", "quantity": 1, "unit": "piece"},
    )
    assert bad_pantry.status_code == 422

    with pytest.raises(ValueError, match="missing id, name, or description"):
        validate_catalogue_payload(
            {
                "ingredients": [{"id": "ing_1", "canonical_name": "test", "category": "veg"}],
                "recipes": [{"id": "r1", "name": "", "description": "bad"}],
            }
        )
