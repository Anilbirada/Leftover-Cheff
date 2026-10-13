# Risks and Mitigations — Leftover Chef

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Implemented |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | Users assume an ingredient in the digital pantry with a future best-before date is automatically safe to eat. | Medium | High | Every pantry item and recipe detail response includes an explicit food-safety warning stating that digital records and dates never prove physical food safety (**TC-43**). |
| **R-02** | String matching merges ingredients with different allergen or culinary properties (e.g., `milk` vs `coconut milk`, `wheat flour` vs `rice flour`, `peanuts` vs `tree nuts`). | Medium | High | Canonical ingredient dictionary and alias table explicitly separate these pairs; fuzzy substring guessing is disabled (**TC-08**). |
| **R-03** | Users treat dietary tags or unverified recipes as medically allergy-safe. | Low | High | Unverified allergen components trigger `"Allergen information not verified"` notices; cross-contamination caveats are shown on every recipe (**TC-40**, **TC-41**). |
| **R-04** | Incompatible shopping list units (`g` vs `cup`) get summed into nonsensical numbers. | Medium | Medium | `scaler.py` checks unit dimensions before combining and keeps incompatible units as separate shopping list lines (**TC-26**, **TC-38**). |
| **R-05** | External AI provider outage breaks recipe search. | Medium | Low | Core search is 100% local and deterministic; optional assistant explanations fall back cleanly to deterministic summaries (**TC-50**). |

---
**Developed by Anil Biradar**
