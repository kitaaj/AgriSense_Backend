from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RecommendationService:
    """
    Service for generating farming recommendations and health scores
    based on a comprehensive iSDA soil analysis.
    """
    
    def __init__(self):
        # Optimal ranges for key soil properties. Units are critical here.
        # These are general values and can be customized for specific crops.
        self.optimal_ranges = {
            "ph": {"min": 6.0, "max": 7.2, "unit": None},
            "carbon_organic": {"min": 1.5, "max": 3.0, "unit": "%"}, # Converted from g/kg
            "nitrogen_total": {"min": 0.15, "max": 0.3, "unit": "%"}, # Converted from g/kg
            "phosphorous_extractable": {"min": 25, "max": 50, "unit": "ppm"}, # ppm is same as mg/kg
            "potassium_extractable": {"min": 150, "max": 300, "unit": "ppm"},
            "cation_exchange_capacity": {"min": 10, "max": 25, "unit": "cmol(+)/kg"},
            "sulphur_extractable": {"min": 10, "max": 20, "unit": "ppm"},
            "zinc_extractable": {"min": 1.5, "max": 5.0, "unit": "ppm"},
        }

    def _get_value_from_properties(self, properties: Dict, prop_name: str, depth: str) -> Optional[Any]:
        """Helper to safely extract a single value for a given property and depth."""
        try:
            property_layers = properties.get(prop_name, [])
            for layer in property_layers:
                if layer.get("depth", {}).get("value") == depth:
                    return layer.get("value", {}).get("value")
            return None
        except (AttributeError, TypeError):
            return None

    def generate_recommendations(
        self, 
        soil_properties: Dict, 
        crop_type: Optional[str] = None,
        depth: str = "0-20"
    ) -> List[Dict]:
        """
        Generate recommendations for a specific soil depth based on the full analysis.
        """
        recommendations = []
        
        # A map of property names to their analysis functions
        analysis_functions = {
            "ph": self._analyze_ph,
            "carbon_organic": self._analyze_organic_carbon,
            "nitrogen_total": self._analyze_nitrogen,
            "phosphorous_extractable": self._analyze_phosphorus,
            "potassium_extractable": self._analyze_potassium,
            "cation_exchange_capacity": self._analyze_cec,
            "sulphur_extractable": self._analyze_sulphur,
            "zinc_extractable": self._analyze_zinc,
            "texture_class": self._analyze_texture,
        }

        for prop_name, func in analysis_functions.items():
            value = self._get_value_from_properties(soil_properties, prop_name, depth)
            if value is not None:
                rec = func(value)
                if rec:
                    recommendations.extend(rec)
            
        recommendations.sort(key=lambda x: x.get("priority", 5))
        return recommendations

    def get_soil_health_score(self, soil_properties: Dict, depth: str = "0-20") -> Dict:
        """Calculate overall soil health score based on key properties at a specific depth."""
        scores = {}
        total_score = 0
        property_count = 0
        
        for prop, optimal in self.optimal_ranges.items():
            value = self._get_value_from_properties(soil_properties, prop, depth)
            if value is not None:
                # CRITICAL: Handle unit conversions before scoring
                original_unit = soil_properties.get(prop, [{}])[0].get("value", {}).get("unit")
                if original_unit == "g/kg" and optimal["unit"] == "%":
                    value /= 10
                
                score = self._calculate_property_score(value, optimal["min"], optimal["max"])
                scores[prop] = round(score)
                total_score += score
                property_count += 1
        
        overall_score = total_score / property_count if property_count > 0 else 0
        
        if overall_score >= 80: health_category = "Excellent"
        elif overall_score >= 60: health_category = "Good"
        elif overall_score >= 40: health_category = "Fair"
        else: health_category = "Poor"
        
        return {
            "overall_score": round(overall_score),
            "health_category": health_category,
            "property_scores": scores,
            "analysis_depth": depth
        }

    def _calculate_property_score(self, value: float, min_val: float, max_val: float) -> float:
        """Generic function to calculate a score from 0 to 100 based on an optimal range."""
        if min_val <= value <= max_val:
            return 100
        elif value < min_val:
            # Score decreases from 100 to 0 as value moves from min_val to 0.
            return max(0, 100 * (value / min_val))
        else: # value > max_val
            # Score decreases from 100 to 0 as value moves from max_val to 2*max_val.
            return max(0, 100 * (1 - (value - max_val) / max_val))
            
    # --- Individual Property Analysis Methods ---

    def _analyze_ph(self, value: float) -> List[Dict]:
        if value < 5.5:
            return [{"type": "amendment", "title": "Correct Low pH", "description": f"Soil pH is {value:.1f}, which is very acidic. Apply agricultural lime to raise the pH. This improves nutrient availability and reduces potential aluminum toxicity.", "priority": 1}]
        if value > 7.8:
            return [{"type": "amendment", "title": "Correct High pH", "description": f"Soil pH is {value:.1f}, which is alkaline. Apply elemental sulfur or use acidifying fertilizers (like ammonium sulfate) to lower the pH.", "priority": 1}]
        return []

    def _analyze_organic_carbon(self, value: float) -> List[Dict]:
        # The value from API is in g/kg. Convert to % by dividing by 10.
        value_percent = value / 10
        if value_percent < 1.0:
            return [{"type": "management", "title": "Increase Organic Matter", "description": f"Organic Carbon is low at {value_percent:.2f}%. Incorporate compost, manure, cover crops, or crop residues to improve soil structure, water retention, and fertility.", "priority": 2}]
        return []

    def _analyze_nitrogen(self, value: float) -> List[Dict]:
        # The value from API is in g/kg. Convert to % by dividing by 10.
        value_percent = value / 10
        if value_percent < 0.1:
            return [{"type": "fertilizer", "title": "Apply Nitrogen (N)", "description": f"Total Nitrogen is very low at {value_percent:.2f}%. Apply a nitrogen-based fertilizer. Consider split applications to match crop needs and reduce loss.", "priority": 1}]
        return []

    def _analyze_phosphorus(self, value: float) -> List[Dict]:
        if value < 20:
            return [{"type": "fertilizer", "title": "Apply Phosphorus (P)", "description": f"Extractable Phosphorus is low at {value:.1f} ppm. Apply a phosphorus fertilizer (e.g., MAP, DAP) at planting to support root development.", "priority": 2}]
        return []

    def _analyze_potassium(self, value: float) -> List[Dict]:
        if value < 120:
            return [{"type": "fertilizer", "title": "Apply Potassium (K)", "description": f"Extractable Potassium is low at {value:.1f} ppm. Apply a potassium fertilizer (e.g., MOP, SOP) to improve plant vigor and stress resistance.", "priority": 2}]
        return []
    
    def _analyze_cec(self, value: float) -> List[Dict]:
        if value < 8:
            return [{"type": "insight", "title": "Low Nutrient Holding Capacity", "description": f"Cation Exchange Capacity (CEC) is low at {value:.1f} cmol(+)/kg. This indicates a sandy or low-organic matter soil that struggles to retain nutrients. Frequent, small applications of fertilizer are more effective than single large ones. Building organic matter is key.", "priority": 3}]
        return []

    def _analyze_sulphur(self, value: float) -> List[Dict]:
        if value < 8:
            return [{"type": "fertilizer", "title": "Apply Sulphur (S)", "description": f"Sulphur level is low at {value:.1f} ppm. Consider using sulphur-containing fertilizers like ammonium sulphate or gypsum.", "priority": 3}]
        return []

    def _analyze_zinc(self, value: float) -> List[Dict]:
        if value < 1.0:
            return [{"type": "micronutrient", "title": "Apply Zinc (Zn)", "description": f"Zinc level is low at {value:.1f} ppm. A foliar spray or soil application of a zinc supplement may be needed, especially for sensitive crops like maize.", "priority": 4}]
        return []
        
    def _analyze_texture(self, value: str) -> List[Dict]:
        if "Clay" in value:
            return [{"type": "management", "title": "Manage Clay Texture", "description": f"Soil texture is '{value}'. Clay soils have excellent water and nutrient retention but can be prone to compaction and poor drainage. Avoid working the soil when wet and incorporate organic matter to improve structure.", "priority": 5}]
        if "Sandy" in value:
            return [{"type": "management", "title": "Manage Sandy Texture", "description": f"Soil texture is '{value}'. Sandy soils have excellent drainage but poor water and nutrient retention. Frequent irrigation and split fertilizer applications are recommended. Building organic matter is critical.", "priority": 5}]
        return []


# Global instance for the service
recommendation_service = RecommendationService()