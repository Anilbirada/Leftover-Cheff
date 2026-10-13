# Food Safety and Allergen Limitations — Leftover Chef

## 1. Core Food-Safety Principles
Leftover Chef enforces strict boundaries between digital inventory convenience and physical food safety:
1. **Digital Pantry Records Do Not Prove Safety**: Adding an ingredient to My Pantry or recording a future `best_before_date` never proves that an item is safe to eat (**TC-43**).
2. **Physical Inspection & Storage Conditions**: Users are explicitly reminded on every pantry item and recipe detail view to inspect ingredients for spoilage, off-odours, mould, sliminess, or unsafe temperature exposure before cooking.
3. **Cooking Does Not Make Spoiled Food Safe**: Heat treatment cannot neutralize all heat-stable toxins produced by bacteria or mould in spoiled food.

## 2. Allergen Verification & Labelling Rules
1. **Verified vs Unverified Allergen Metadata**:
   - Each recipe's allergen declarations include a `verification_status` (`"verified"` vs `"unverified"`).
   - If a recipe contains any unverified allergen component (for example, commercial soy sauce in `rec_spring_onion_soy_fried_rice` where wheat content depends on the specific brand), the application displays `"Allergen information not verified"` (**TC-41**).
2. **Cross-Contamination & Brand Variations**:
   - Even when base recipe ingredients are audited against major allergens, commercial spice blends, cooking oils, and shared home kitchen equipment can introduce cross-contamination (**TC-40**).
3. **No Silent Allergen Substitutions**:
   - The matching engine never silently substitutes dairy milk for coconut milk, wheat flour for rice flour, or peanuts for tree nuts (**TC-08**).
4. **Dietary Filters Are Not Medical Advice**:
   - User dietary preferences and excluded ingredients act strictly as search filters and are accompanied by a medical disclaimer.

---
**Developed by Anil Biradar**
