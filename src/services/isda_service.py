import requests
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ISDAService:
    """
    Service for interacting with the iSDAsoil API.
    Refactored for efficiency and full data coverage.
    """
    
    def __init__(self):
        self.base_url = "https://api.isda-africa.com"
        self.access_token = None
        self.token_expires_at = None
        
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with iSDA API and get an access token."""
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{self.base_url}/login", data=payload, timeout=30)
            
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            data = response.json()
            self.access_token = data.get("access_token")
            # Token expires in 60 minutes, refresh a bit earlier
            self.token_expires_at = datetime.utcnow() + timedelta(minutes=55)
            logger.info("Successfully authenticated with iSDA API")
            return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired."""
        return (
            self.access_token is not None and 
            self.token_expires_at is not None and 
            datetime.utcnow() < self.token_expires_at
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with the authorization token."""
        if not self._is_token_valid():
            # This should ideally be handled by re-authenticating.
            # For simplicity, we raise an error to be caught by the calling function.
            raise ConnectionError("No valid access token. Please authenticate first.")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_available_layers(self) -> Optional[Dict]:
        """Get metadata about available soil property layers."""
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/isdasoil/v2/layers", headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting iSDA layers: {e}")
            return None
    
    def get_all_soil_properties(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Get all available soil properties for a specific location in a single API call.
        This is the primary method to fetch soil data.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
        
        Returns:
            A dictionary containing the full soil property data or None if failed.
        """
        try:
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            
            headers = self._get_headers()
            params = {"lat": latitude, "lon": longitude}
            
            # By not specifying a 'property' or 'depth', the API returns all available data.
            response = requests.get(
                f"{self.base_url}/isdasoil/v2/soilproperty",
                headers=headers,
                params=params,
                timeout=45  # Increased timeout for potentially larger response
            )
            
            response.raise_for_status()
            return response.json()
                
        except (ValueError, requests.exceptions.RequestException) as e:
            logger.error(f"Error getting all soil properties: {e}")
            return None
    
    @staticmethod
    def extract_property_data(
        soil_data: Dict[str, Any], 
        property_name: str, 
        depth: str = "0-20"
    ) -> Optional[Dict[str, Any]]:
        """
        Extracts the data block for a specific property and depth from the full API response.

        Args:
            soil_data: The full JSON response from the iSDA API.
            property_name: The name of the property to extract (e.g., "ph").
            depth: The specific depth required (e.g., "0-20", "20-50").

        Returns:
            A dictionary with the property data or None if not found.
        """
        try:
            # The main data is nested under the 'property' key
            properties = soil_data.get("property", {})
            property_layers = properties.get(property_name, [])
            
            for layer in property_layers:
                if layer.get("depth", {}).get("value") == depth:
                    return layer
            return None
        except Exception as e:
            logger.error(f"Error extracting property data for '{property_name}' at depth '{depth}': {e}")
            return None

    @staticmethod
    def extract_value(property_data: Dict[str, Any]) -> Optional[Any]:
        """Extracts the main value from a single property data block."""
        try:
            return property_data.get("value", {}).get("value")
        except AttributeError:
            # Handles case where property_data is None
            return None

# Global instance for the service
isda_service = ISDAService()