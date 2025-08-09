from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.farm import Farm
from src.models.soil_analysis import SoilAnalysis, Recommendation
from src.services.isda_service import isda_service
from src.services.recommendation_service import recommendation_service
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

soil_bp = Blueprint('soil', __name__)

# It's crucial to use environment variables for credentials in production
ISDA_USERNAME = os.getenv('ISDA_USERNAME', 'your_isda_username')
ISDA_PASSWORD = os.getenv('ISDA_PASSWORD', 'your_isda_password')

def _authenticate_isda():
    """Helper function to handle iSDA authentication."""
    if not isda_service._is_token_valid():
        if not isda_service.authenticate(ISDA_USERNAME, ISDA_PASSWORD):
            return False
    return True

@soil_bp.route('/farms/<int:farm_id>/soil-analysis', methods=['POST'])
@jwt_required()
def analyze_soil(farm_id):
    """
    Perform a comprehensive soil analysis for a farm using the iSDA API.
    This endpoint now fetches all available soil data in a single API call.
    """
    try:
        current_user_id = int(get_jwt_identity())
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        if not farm:
            return jsonify({'error': 'Farm not found or unauthorized'}), 404
        
        data = request.get_json() or {}
        latitude = data.get('latitude', farm.latitude)
        longitude = data.get('longitude', farm.longitude)
        
        try:
            latitude, longitude = float(latitude), float(longitude)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Invalid coordinates.")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid or missing latitude/longitude'}), 400
        
        # Ensure we are authenticated with the iSDA service
        if not _authenticate_isda():
            return jsonify({'error': 'Failed to authenticate with external soil data service'}), 503
        
        # Fetch all soil properties in a single, efficient call
        soil_data_full = isda_service.get_all_soil_properties(latitude, longitude)
        if not soil_data_full or "property" not in soil_data_full:
            return jsonify({'error': 'Failed to retrieve soil data from the service'}), 503
        
        # The 'property' object contains the rich data we want to save and analyze
        soil_properties = soil_data_full["property"]
        
        # Save the complete analysis to the database
        soil_analysis = SoilAnalysis()
        
        soil_analysis.farm_id=farm_id,
        soil_analysis.latitude=latitude,
        soil_analysis.longitude=longitude,
        # The JSON field now stores the entire 'property' object
        soil_analysis.soil_properties=soil_properties,
        soil_analysis.analyzed_at=datetime.utcnow()
        
        db.session.add(soil_analysis)
        db.session.flush()  # Flush to get the new soil_analysis.id

        # Generate recommendations based on the full topsoil (0-20cm) data
        recommendations_data = recommendation_service.generate_recommendations(
            soil_properties, 
            crop_type=farm.crop_type,
            depth="0-20"  # Specify topsoil for main recommendations
        )
        
        # Save recommendations
        for rec_data in recommendations_data:
            rec_data['soil_analysis_id'] = soil_analysis.id
            db.session.add(Recommendation(**rec_data))
        
        db.session.commit()
        
        # Calculate soil health score for the topsoil
        health_score = recommendation_service.get_soil_health_score(soil_properties, depth="0-20")
        
        return jsonify({
            'message': 'Soil analysis completed successfully',
            'analysis_id': soil_analysis.id,
            'health_score': health_score,
            'recommendations': recommendations_data,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Soil analysis endpoint error: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred during soil analysis'}), 500

# Other endpoints (get_farm_soil_analyses, get_soil_analysis, etc.) remain largely
# the same but will now benefit from the richer data stored in the database.
# A small adjustment to get_soil_analysis is shown below.

@soil_bp.route('/soil-analyses/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_soil_analysis(analysis_id):
    """Get a specific soil analysis with its stored properties, recommendations, and health score."""
    try:
        current_user_id = int(get_jwt_identity())
        analysis = SoilAnalysis.query.join(Farm).filter(
            SoilAnalysis.id == analysis_id, Farm.user_id == current_user_id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Soil analysis not found or unauthorized'}), 404
        
        # Recalculate health score on-the-fly or store it. Here we recalculate.
        health_score = recommendation_service.get_soil_health_score(analysis.soil_properties, depth="0-20")
        
        return jsonify({
            'analysis': analysis.to_dict(), # Assumes to_dict() correctly serializes the object
            'recommendations': [rec.to_dict() for rec in analysis.recommendations],
            'health_score': health_score
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soil analysis {analysis_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve soil analysis'}), 500
        
# The /isda/layers endpoint is still useful and remains unchanged.
@soil_bp.route('/isda/layers', methods=['GET'])
@jwt_required()
def get_isda_layers():
    """Get available soil property layers from iSDA API."""
    try:
        if not _authenticate_isda():
            return jsonify({'error': 'Failed to authenticate with soil data service'}), 503
        
        layers_data = isda_service.get_available_layers()
        if not layers_data:
            return jsonify({'error': 'Failed to retrieve layers data'}), 503
        
        return jsonify(layers_data), 200
        
    except Exception as e:
        logger.error(f"Error getting iSDA layers: {e}")
        return jsonify({'error': 'Failed to get layers data'}), 500