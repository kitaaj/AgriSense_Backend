import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ISDAService:
    """Service for interacting with iSDA Africa soil data API"""
    
    def __init__(self):
        self.base_url = "https://api.isda-africa.com"
        self.access_token = None
        self.token_expires_at = None
        
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with iSDA API and get access token"""
        try:
            payload = {
                "username": username,
                "password": password
            }
            
            response = requests.post(
                f"{self.base_url}/login",
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                # Token expires in 60 minutes according to docs
                self.token_expires_at = datetime.utcnow() + timedelta(minutes=55)
                logger.info("Successfully authenticated with iSDA API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired"""
        return (
            self.access_token is not None and 
            self.token_expires_at is not None and 
            datetime.utcnow() < self.token_expires_at
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        if not self._is_token_valid():
            raise Exception("No valid access token. Please authenticate first.")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_available_layers(self) -> Optional[Dict]:
        """Get metadata about available soil property layers"""
        try:
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/isdasoil/v2/layers",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get layers: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting layers: {str(e)}")
            return None
    
    def get_soil_properties(
        self, 
        latitude: float, 
        longitude: float, 
        depth: Optional[str] = None,
        property_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get soil properties for a specific location
        
        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            depth: Soil depth (e.g., "0-20", "20-50", "0-50", "0-200")
            property_name: Specific property to retrieve (e.g., "ph", "carbon_organic")
        
        Returns:
            Dictionary containing soil property data or None if failed
        """
        try:
            # Validate coordinates
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            
            headers = self._get_headers()
            
            # Build query parameters
            params = {
                "lat": latitude,
                "lon": longitude
            }
            
            if depth:
                params["depth"] = depth
            if property_name:
                params["property"] = property_name
            
            response = requests.get(
                f"{self.base_url}/isdasoil/v2/soilproperty",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get soil properties: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting soil properties: {str(e)}")
            return None
    
    def get_comprehensive_soil_analysis(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict]:
        """
        Get comprehensive soil analysis for key agricultural properties
        
        Returns data for pH, organic carbon, nitrogen, phosphorus, potassium
        at 0-20cm depth (topsoil)
        """
        try:
            key_properties = [
                "ph",
                "carbon_organic", 
                "nitrogen_total",
                "phosphorous_extractable",
                "potassium_extractable"
            ]
            
            results = {}
            
            for prop in key_properties:
                data = self.get_soil_properties(
                    latitude=latitude,
                    longitude=longitude,
                    depth="0-20",
                    property_name=prop
                )
                
                if data and "property" in data:
                    results[prop] = data["property"].get(prop, [])
            
            return {
                "latitude": latitude,
                "longitude": longitude,
                "depth": "0-20",
                "properties": results,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis: {str(e)}")
            return None
    
    def extract_property_value(self, property_data: List[Dict]) -> Optional[float]:
        """Extract the main value from iSDA property data structure"""
        try:
            if property_data and len(property_data) > 0:
                value_data = property_data[0].get("value", {})
                return value_data.get("value")
            return None
        except Exception as e:
            logger.error(f"Error extracting property value: {str(e)}")
            return None
    
    def extract_property_uncertainty(self, property_data: List[Dict]) -> Optional[Tuple[float, float]]:
        """Extract uncertainty bounds from iSDA property data"""
        try:
            if property_data and len(property_data) > 0:
                uncertainty_data = property_data[0].get("uncertainty", [])
                if len(uncertainty_data) > 1:
                    bounds = uncertainty_data[1]
                    return (bounds.get("lower_bound"), bounds.get("upper_bound"))
            return None
        except Exception as e:
            logger.error(f"Error extracting uncertainty: {str(e)}")
            return None

# Global instance for the service
isda_service = ISDAService()

