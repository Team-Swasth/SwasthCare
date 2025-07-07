"""
Simple and reliable AI features for SwasthCare
Focus on accuracy and practical utility
"""

from django.conf import settings
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json
import re


def analyze_ingredients_for_allergens(product_json, user_allergies=None):
    """
    Analyze product ingredients for allergens and health concerns
    This is highly reliable as it works with actual ingredient lists
    """
    ingredients = product_json.get('ingredients', product_json.get('Ingredients', ''))
    if not ingredients:
        return {"error": "No ingredient information available"}
    
    # Common allergens to check for
    common_allergens = [
        'milk', 'eggs', 'fish', 'shellfish', 'tree nuts', 'peanuts', 
        'wheat', 'soybeans', 'sesame', 'gluten', 'lactose'
    ]
    
    # Simple text-based allergen detection (very reliable)
    found_allergens = []
    ingredients_lower = ingredients.lower()
    
    for allergen in common_allergens:
        if allergen in ingredients_lower:
            found_allergens.append(allergen)
    
    # Check for user-specific allergies
    user_allergen_warnings = []
    if user_allergies:
        for allergy in user_allergies:
            if allergy.lower() in ingredients_lower:
                user_allergen_warnings.append(allergy)
    
    return {
        "ingredients": ingredients,
        "common_allergens_found": found_allergens,
        "user_allergen_warnings": user_allergen_warnings,
        "allergen_info": product_json.get('allergen_info', 'Not specified'),
        "safe_for_user": len(user_allergen_warnings) == 0
    }


def get_simple_health_score(product_json):
    """
    Calculate a simple health score based on nutritional values
    Very reliable as it uses actual nutritional data
    """
    try:
        nutrition = product_json.get('nutritional_info', {})
        if not nutrition:
            return {"error": "No nutritional information available"}
        
        score = 5  # Start with neutral score
        reasons = []
        
        # Positive factors
        protein = float(nutrition.get('protein_g', 0))
        if protein > 10:
            score += 1
            reasons.append("High protein content")
        
        fiber = float(nutrition.get('fiber_g', 0))
        if fiber > 3:
            score += 1
            reasons.append("Good fiber content")
        
        # Negative factors
        sugar = float(nutrition.get('sugars_g', 0))
        if sugar > 15:
            score -= 1
            reasons.append("High sugar content")
        
        sodium = float(nutrition.get('sodium_mg', 0))
        if sodium > 600:
            score -= 1
            reasons.append("High sodium content")
        
        saturated_fat = float(nutrition.get('saturated_fat_g', 0))
        if saturated_fat > 5:
            score -= 1
            reasons.append("High saturated fat")
        
        trans_fat = float(nutrition.get('trans_fat_g', 0))
        if trans_fat > 0:
            score -= 2
            reasons.append("Contains trans fat")
        
        # Ensure score is between 1-10
        score = max(1, min(10, score))
        
        return {
            "health_score": score,
            "max_score": 10,
            "factors": reasons,
            "recommendation": get_score_recommendation(score)
        }
    
    except Exception as e:
        return {"error": f"Could not calculate health score: {str(e)}"}


def get_score_recommendation(score):
    """Get recommendation based on health score"""
    if score >= 8:
        return "Excellent choice! This product has a great nutritional profile."
    elif score >= 6:
        return "Good choice! This product is generally healthy."
    elif score >= 4:
        return "Moderate choice. Consider the nutritional factors mentioned."
    else:
        return "Consider healthier alternatives if possible."


def check_dietary_compatibility(product_json, dietary_preferences=None):
    """
    Check if product is compatible with dietary preferences
    Very reliable as it works with actual ingredient data
    """
    if not dietary_preferences:
        return {"compatible": True, "message": "No dietary restrictions specified"}
    
    ingredients = product_json.get('ingredients', product_json.get('Ingredients', '')).lower()
    special_diet = product_json.get('special_diet', [])
    
    compatibility_results = {}
    
    for preference in dietary_preferences:
        preference_lower = preference.lower()
        compatible = True
        reason = ""
        
        if preference_lower == 'vegetarian':
            meat_indicators = ['chicken', 'beef', 'pork', 'fish', 'meat', 'gelatin']
            for indicator in meat_indicators:
                if indicator in ingredients:
                    compatible = False
                    reason = f"Contains {indicator}"
                    break
        
        elif preference_lower == 'vegan':
            animal_products = ['milk', 'eggs', 'honey', 'cheese', 'butter', 'cream', 'whey', 'casein']
            for product in animal_products:
                if product in ingredients:
                    compatible = False
                    reason = f"Contains {product}"
                    break
        
        elif preference_lower == 'gluten-free':
            gluten_sources = ['wheat', 'barley', 'rye', 'malt', 'gluten']
            for source in gluten_sources:
                if source in ingredients:
                    compatible = False
                    reason = f"Contains {source}"
                    break
        
        elif preference_lower == 'keto':
            # Simple carb check for keto
            carbs = float(product_json.get('nutritional_info', {}).get('carbohydrate_g', 0))
            if carbs > 5:  # Per serving
                compatible = False
                reason = f"High carbohydrates ({carbs}g)"
        
        compatibility_results[preference] = {
            "compatible": compatible,
            "reason": reason if not compatible else "Compatible"
        }
    
    return compatibility_results


def get_simple_product_insights(product_json, user_profile=None):
    """
    Get comprehensive but simple product insights
    Combines all the reliable analysis functions
    """
    insights = {
        "product_name": product_json.get('prod_name', 'Unknown'),
        "barcode": product_json.get('barcode', 'Unknown')
    }
    
    # Health score analysis
    health_analysis = get_simple_health_score(product_json)
    insights["health_analysis"] = health_analysis
    
    # Allergen analysis
    user_allergies = user_profile.get('allergies', []) if user_profile else []
    allergen_analysis = analyze_ingredients_for_allergens(product_json, user_allergies)
    insights["allergen_analysis"] = allergen_analysis
    
    # Dietary compatibility
    dietary_preferences = user_profile.get('dietary_preferences', []) if user_profile else []
    dietary_analysis = check_dietary_compatibility(product_json, dietary_preferences)
    insights["dietary_analysis"] = dietary_analysis
    
    return insights
