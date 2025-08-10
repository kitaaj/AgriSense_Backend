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
ISDA_USERNAME = os.getenv('ISDA_USERNAME', 'default_username')
ISDA_PASSWORD = os.getenv('ISDA_PASSWORD', 'default_password')

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
        analysis_depth = data.get('depth', '0-20')
        
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
        soil_data_full = isda_service.get_all_soil_properties(latitude, longitude, analysis_depth)
        if not soil_data_full or "property" not in soil_data_full:
            return jsonify({'error': 'Failed to retrieve soil data from the service'}), 503
        
        # The 'property' object contains the rich data we want to save and analyze
        soil_properties = soil_data_full["property"]
        
        # Save the complete analysis to the database
        soil_analysis = SoilAnalysis()
        
        soil_analysis.farm_id=farm_id
        soil_analysis.latitude=latitude
        soil_analysis.longitude=longitude
        soil_analysis.depth=analysis_depth
        soil_analysis.soil_properties=soil_properties
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
            'analysis': soil_analysis.to_dict(), 
            'analysis_id': soil_analysis.id,
            'health_score': health_score,
            'recommendations': recommendations_data,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Soil analysis endpoint error: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred during soil analysis'}), 500


@soil_bp.route('/soil-analyses', methods=['GET']) # Note: No <farm_id> in the URL
@jwt_required()
def get_all_user_soil_analyses():
    """
    Get all soil analyses for all farms belonging to the current user.
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        analyses_from_db = SoilAnalysis.query.join(Farm).filter(
            Farm.user_id == current_user_id
        ).order_by(SoilAnalysis.analyzed_at.desc()).all()
        
        results = []
        for analysis in analyses_from_db:
            # Convert the DB object to a dictionary
            analysis_dict = analysis.to_dict()
            
            # Calculate the health score on-the-fly for this analysis
            health_score = recommendation_service.get_soil_health_score(
                analysis.soil_properties,
                analysis.depth
            )
            
            # Add the calculated score to the dictionary
            analysis_dict['health_score'] = health_score
            
            results.append(analysis_dict)
            
        return jsonify({'analyses': results}), 200
        
    except Exception as e:
        logger.error(f"Error getting all user soil analyses: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve soil analyses'}), 500


@soil_bp.route('/farms/<int:farm_id>/soil-analyses', methods=['GET'])
@jwt_required()
def get_farm_soil_analyses(farm_id):
    """Get all soil analyses for a farm"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Verify farm ownership
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get soil analyses with pagination
        analyses = SoilAnalysis.query.filter_by(farm_id=farm_id)\
            .order_by(SoilAnalysis.analyzed_at.desc())\
            .limit(limit).offset(offset).all()
        
        total_count = SoilAnalysis.query.filter_by(farm_id=farm_id).count()
        
        return jsonify({
            'analyses': [analysis.to_dict() for analysis in analyses],
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soil analyses: {str(e)}")
        return jsonify({'error': 'Failed to get soil analyses', 'details': str(e)}), 500


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
        
@soil_bp.route('/soil-analyses/<int:analysis_id>/recommendations', methods=['GET'])
@jwt_required()
def get_analysis_recommendations(analysis_id):
    """Get recommendations for a specific soil analysis"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get soil analysis and verify ownership
        analysis = SoilAnalysis.query.join(Farm)\
            .filter(SoilAnalysis.id == analysis_id, Farm.user_id == current_user_id)\
            .first()
        
        if not analysis:
            return jsonify({'error': 'Soil analysis not found'}), 404
        
        # Get recommendations sorted by priority
        recommendations = Recommendation.query.filter_by(soil_analysis_id=analysis_id)\
            .order_by(Recommendation.priority.asc()).all()
        
        return jsonify({
            'recommendations': [rec.to_dict() for rec in recommendations],
            'analysis_id': analysis_id,
            'total': len(recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': 'Failed to get recommendations', 'details': str(e)}), 500


@soil_bp.route('/farms/<int:farm_id>/soil-health-summary', methods=['GET'])
@jwt_required()
def get_farm_soil_health_summary(farm_id):
    """Get soil health summary for a farm"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Verify farm ownership
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        # Get latest soil analysis
        latest_analysis = SoilAnalysis.query.filter_by(farm_id=farm_id)\
            .order_by(SoilAnalysis.analyzed_at.desc()).first()
        
        if not latest_analysis:
            return jsonify({
                'message': 'No soil analysis available for this farm',
                'farm_id': farm_id,
                'has_analysis': False
            }), 200
        
        # Calculate health score
        health_score = recommendation_service.get_soil_health_score(latest_analysis.soil_properties)
        
        # Get high priority recommendations count
        high_priority_count = Recommendation.query.filter_by(
            soil_analysis_id=latest_analysis.id
        ).filter(Recommendation.priority <= 2).count()
        
        # Get total analyses count
        total_analyses = SoilAnalysis.query.filter_by(farm_id=farm_id).count()
        
        return jsonify({
            'farm_id': farm_id,
            'has_analysis': True,
            'latest_analysis_date': latest_analysis.analyzed_at.isoformat(),
            'health_score': health_score,
            'high_priority_recommendations': high_priority_count,
            'total_analyses': total_analyses
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soil health summary: {str(e)}")
        return jsonify({'error': 'Failed to get soil health summary', 'details': str(e)}), 500



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