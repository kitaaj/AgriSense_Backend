from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service for generating farming recommendations based on soil analysis"""
    
    def __init__(self):
        # Optimal ranges for key soil properties
        self.optimal_ranges = {
            "ph": {"min": 6.0, "max": 7.5, "unit": "pH"},
            "carbon_organic": {"min": 2.0, "max": 4.0, "unit": "%"},
            "nitrogen_total": {"min": 0.2, "max": 0.5, "unit": "%"},
            "phosphorous_extractable": {"min": 20, "max": 50, "unit": "mg/kg"},
            "potassium_extractable": {"min": 150, "max": 300, "unit": "mg/kg"}
        }
    
    def generate_recommendations(
        self, 
        soil_properties: Dict, 
        crop_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate farming recommendations based on soil analysis
        
        Args:
            soil_properties: Dictionary containing soil property values
            crop_type: Type of crop being grown (optional)
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        try:
            # Analyze pH levels
            ph_recommendations = self._analyze_ph(soil_properties.get("ph", []))
            recommendations.extend(ph_recommendations)
            
            # Analyze organic carbon
            carbon_recommendations = self._analyze_organic_carbon(soil_properties.get("carbon_organic", []))
            recommendations.extend(carbon_recommendations)
            
            # Analyze nitrogen
            nitrogen_recommendations = self._analyze_nitrogen(soil_properties.get("nitrogen_total", []))
            recommendations.extend(nitrogen_recommendations)
            
            # Analyze phosphorus
            phosphorus_recommendations = self._analyze_phosphorus(soil_properties.get("phosphorous_extractable", []))
            recommendations.extend(phosphorus_recommendations)
            
            # Analyze potassium
            potassium_recommendations = self._analyze_potassium(soil_properties.get("potassium_extractable", []))
            recommendations.extend(potassium_recommendations)
            
            # Sort by priority (1 = highest priority)
            recommendations.sort(key=lambda x: x.get("priority", 5))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _extract_value(self, property_data: List[Dict]) -> Optional[float]:
        """Extract value from iSDA property data structure"""
        try:
            if property_data and len(property_data) > 0:
                value_data = property_data[0].get("value", {})
                return value_data.get("value")
            return None
        except:
            return None
    
    def _analyze_ph(self, ph_data: List[Dict]) -> List[Dict]:
        """Analyze pH levels and generate recommendations"""
        recommendations = []
        ph_value = self._extract_value(ph_data)
        
        if ph_value is None:
            return recommendations
        
        if ph_value < 5.5:
            recommendations.append({
                "type": "amendment",
                "title": "Apply Lime",
                "description": f"Soil pH is {ph_value:.1f}, which is too acidic. Apply agricultural lime to raise pH to optimal range (6.0-7.5). This will improve nutrient availability and reduce aluminum toxicity.",
                "dosage": "2-4 tons per hectare",
                "timing": "Apply 3-4 months before planting",
                "priority": 1
            })
        elif ph_value > 8.0:
            recommendations.append({
                "type": "amendment",
                "title": "Apply Sulfur",
                "description": f"Soil pH is {ph_value:.1f}, which is too alkaline. Apply elemental sulfur to lower pH to optimal range (6.0-7.5).",
                "dosage": "200-500 kg per hectare",
                "timing": "Apply 2-3 months before planting",
                "priority": 1
            })
        
        return recommendations
    
    def _analyze_organic_carbon(self, carbon_data: List[Dict]) -> List[Dict]:
        """Analyze organic carbon levels and generate recommendations"""
        recommendations = []
        carbon_value = self._extract_value(carbon_data)
        
        if carbon_value is None:
            return recommendations
        
        if carbon_value < 1.5:
            recommendations.append({
                "type": "amendment",
                "title": "Add Organic Matter",
                "description": f"Organic carbon is {carbon_value:.1f}%, which is low. Incorporate compost, manure, or crop residues to improve soil structure and fertility.",
                "dosage": "5-10 tons compost per hectare",
                "timing": "Apply before planting season",
                "priority": 2
            })
        
        return recommendations
    
    def _analyze_nitrogen(self, nitrogen_data: List[Dict]) -> List[Dict]:
        """Analyze nitrogen levels and generate recommendations"""
        recommendations = []
        nitrogen_value = self._extract_value(nitrogen_data)
        
        if nitrogen_value is None:
            return recommendations
        
        if nitrogen_value < 0.15:
            recommendations.append({
                "type": "fertilizer",
                "title": "Apply Nitrogen Fertilizer",
                "description": f"Total nitrogen is {nitrogen_value:.2f}%, which is low. Apply nitrogen fertilizer to support crop growth.",
                "dosage": "100-150 kg N per hectare",
                "timing": "Split application: 1/3 at planting, 2/3 at 6 weeks",
                "priority": 2
            })
        
        return recommendations
    
    def _analyze_phosphorus(self, phosphorus_data: List[Dict]) -> List[Dict]:
        """Analyze phosphorus levels and generate recommendations"""
        recommendations = []
        phosphorus_value = self._extract_value(phosphorus_data)
        
        if phosphorus_value is None:
            return recommendations
        
        if phosphorus_value < 15:
            recommendations.append({
                "type": "fertilizer",
                "title": "Apply Phosphorus Fertilizer",
                "description": f"Available phosphorus is {phosphorus_value:.1f} mg/kg, which is low. Apply phosphorus fertilizer to support root development and flowering.",
                "dosage": "40-60 kg P2O5 per hectare",
                "timing": "Apply at planting",
                "priority": 2
            })
        
        return recommendations
    
    def _analyze_potassium(self, potassium_data: List[Dict]) -> List[Dict]:
        """Analyze potassium levels and generate recommendations"""
        recommendations = []
        potassium_value = self._extract_value(potassium_data)
        
        if potassium_value is None:
            return recommendations
        
        if potassium_value < 100:
            recommendations.append({
                "type": "fertilizer",
                "title": "Apply Potassium Fertilizer",
                "description": f"Available potassium is {potassium_value:.1f} mg/kg, which is low. Apply potassium fertilizer to improve disease resistance and water use efficiency.",
                "dosage": "50-80 kg K2O per hectare",
                "timing": "Apply at planting",
                "priority": 3
            })
        
        return recommendations
    
    def get_soil_health_score(self, soil_properties: Dict) -> Dict:
        """Calculate overall soil health score based on key properties"""
        try:
            scores = {}
            total_score = 0
            property_count = 0
            
            # Score each property (0-100 scale)
            for prop, data in soil_properties.items():
                if prop in self.optimal_ranges:
                    value = self._extract_value(data)
                    if value is not None:
                        score = self._calculate_property_score(prop, value)
                        scores[prop] = score
                        total_score += score
                        property_count += 1
            
            overall_score = total_score / property_count if property_count > 0 else 0
            
            # Determine health category
            if overall_score >= 80:
                health_category = "Excellent"
            elif overall_score >= 60:
                health_category = "Good"
            elif overall_score >= 40:
                health_category = "Fair"
            else:
                health_category = "Poor"
            
            return {
                "overall_score": round(overall_score, 1),
                "health_category": health_category,
                "property_scores": scores,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating soil health score: {str(e)}")
            return {"overall_score": 0, "health_category": "Unknown", "property_scores": {}}
    
    def _calculate_property_score(self, property_name: str, value: float) -> float:
        """Calculate score for individual soil property (0-100 scale)"""
        try:
            optimal = self.optimal_ranges.get(property_name)
            if not optimal:
                return 50  # Default score if no optimal range defined
            
            min_val = optimal["min"]
            max_val = optimal["max"]
            
            if min_val <= value <= max_val:
                return 100  # Perfect score within optimal range
            elif value < min_val:
                # Score decreases as value goes below minimum
                if value <= min_val * 0.5:
                    return 0
                else:
                    return 50 * (value / min_val)
            else:
                # Score decreases as value goes above maximum
                if value >= max_val * 2:
                    return 0
                else:
                    return 50 * (max_val / value)
                    
        except Exception as e:
            logger.error(f"Error calculating property score: {str(e)}")
            return 50

# Global instance for the service
recommendation_service = RecommendationService()

