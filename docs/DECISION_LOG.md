# Architecture & Technical Decision Log — Leftover Chef

## ADR-01: Deterministic Backend Matching Engine Instead of LLM-Dependent Search
- **Context**: Recipe search must be reliable, reproducible, fast, and usable offline/locally without requiring paid API keys or hallucinating ingredient matches.
- **Decision**: Implement a pure Python + SQLAlchemy normalisation and matching service (`normalizer.py`, `matcher.py`) backed by explicit canonical ingredient IDs and approved aliases.
- **Consequences**: 100% deterministic scores, sub-10ms matching latency, and zero risk of an LLM conflating allergens like peanuts and tree nuts.

## ADR-02: Explicit Separation of Required vs Optional Ingredients in Score Formula
- **Context**: Including optional garnishes (like chopped coriander leaves) in the required denominator penalises users who have all core ingredients, whereas omitting required spices inflates match scores dishonestly.
- **Decision**: Define `Core Coverage = (matched_required / total_required) * 100`. Keep required spices/oils in the denominator and report optional ingredients separately.
- **Consequences**: Transparent, mathematically verifiable match percentages tested in TC-11, TC-12, TC-13, and TC-16.

## ADR-03: Strict Dimensional Compatibility for Unit Combining
- **Context**: Combining shopping list items across mass (`g`) and volume (`ml` or `cup`) without ingredient-specific density tables produces inaccurate cooking measurements.
- **Decision**: Only merge quantities when units share the same physical dimension (`mass`: `g`/`kg`, `volume`: `ml`/`litre`, `spoon_volume`: `teaspoon`/`tablespoon`). Keep incompatible units as separate shopping list rows.
- **Consequences**: Prevents culinary measurement errors; verified in TC-26 and TC-38.

---
**Developed by Anil Biradar**
