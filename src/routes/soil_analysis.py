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

# iSDA credentials - In production, these should be environment variables
ISDA_USERNAME = os.getenv('ISDA_USERNAME', 'default_username')
ISDA_PASSWORD = os.getenv('ISDA_PASSWORD', 'default_password')

@soil_bp.route('/farms/<int:farm_id>/soil-analysis', methods=['POST'])
@jwt_required()
def analyze_soil(farm_id):
    """Perform soil analysis for a farm using iSDA API"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Verify farm ownership
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        data = request.get_json() or {}
        
        # Use farm coordinates or provided coordinates
        latitude = data.get('latitude', farm.latitude)
        longitude = data.get('longitude', farm.longitude)
        depth = data.get('depth', '0-20')
        
        # Validate coordinates
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            
            if not (-90 <= latitude <= 90):
                return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
            if not (-180 <= longitude <= 180):
                return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
                
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid latitude or longitude format'}), 400
        
        # Authenticate with iSDA API
        if not isda_service._is_token_valid():
            auth_success = isda_service.authenticate(ISDA_USERNAME, ISDA_PASSWORD)
            if not auth_success:
                return jsonify({'error': 'Failed to authenticate with soil data service'}), 503
        
        # Get comprehensive soil analysis from iSDA
        soil_data = isda_service.get_comprehensive_soil_analysis(latitude, longitude)
        
        if not soil_data:
            return jsonify({'error': 'Failed to retrieve soil data'}), 503
        
        # Save soil analysis to database
        soil_analysis = SoilAnalysis()
        
        soil_analysis.farm_id=farm_id
        soil_analysis.latitude=latitude
        soil_analysis.longitude=longitude
        soil_analysis.depth=depth
        soil_analysis.soil_properties=soil_data['properties']
        soil_analysis.analyzed_at=datetime.fromisoformat(soil_data['analyzed_at'])
        
        
        db.session.add(soil_analysis)
        db.session.flush()  # Get the ID
        
        # Generate recommendations
        recommendations_data = recommendation_service.generate_recommendations(
            soil_data['properties'], 
            farm.crop_type
        )
        
        # Save recommendations to database
        for rec_data in recommendations_data:
            recommendation = Recommendation()            
            recommendation.soil_analysis_id=soil_analysis.id
            recommendation.type=rec_data['type']
            recommendation.title=rec_data['title']
            recommendation.description=rec_data['description']
            recommendation.dosage=rec_data.get('dosage')
            recommendation.timing=rec_data.get('timing')
            recommendation.priority=rec_data.get('priority', 3)
            
            db.session.add(recommendation)
        
        db.session.commit()
        
        # Calculate soil health score
        health_score = recommendation_service.get_soil_health_score(soil_data['properties'])
        
        # Query recommendations related to this soil analysis
        recommendations = Recommendation.query.filter_by(soil_analysis_id=soil_analysis.id).all()

        return jsonify({
            'message': 'Soil analysis completed successfully',
            'analysis': soil_analysis.to_dict(),
            'recommendations': [rec.to_dict() for rec in recommendations],
            'health_score': health_score
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Soil analysis error: {str(e)}")
        return jsonify({'error': 'Failed to perform soil analysis', 'details': str(e)}), 500

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
    """Get a specific soil analysis with recommendations"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get soil analysis and verify ownership through farm
        analysis = SoilAnalysis.query.join(Farm)\
            .filter(SoilAnalysis.id == analysis_id, Farm.user_id == current_user_id)\
            .first()
        
        if not analysis:
            return jsonify({'error': 'Soil analysis not found'}), 404
        
        # Calculate current health score
        health_score = recommendation_service.get_soil_health_score(analysis.soil_properties)
        
        return jsonify({
            'analysis': analysis.to_dict(),
            'recommendations': [rec.to_dict() for rec in analysis.recommendations],
            'health_score': health_score
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soil analysis: {str(e)}")
        return jsonify({'error': 'Failed to get soil analysis', 'details': str(e)}), 500

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

@soil_bp.route('/isda/layers', methods=['GET'])
@jwt_required()
def get_isda_layers():
    """Get available soil property layers from iSDA API"""
    try:
        # Authenticate with iSDA API if needed
        if not isda_service._is_token_valid():
            auth_success = isda_service.authenticate(ISDA_USERNAME, ISDA_PASSWORD)
            if not auth_success:
                return jsonify({'error': 'Failed to authenticate with soil data service'}), 503
        
        layers_data = isda_service.get_available_layers()
        
        if not layers_data:
            return jsonify({'error': 'Failed to retrieve layers data'}), 503
        
        return jsonify({
            'layers': layers_data,
            'message': 'Available soil property layers retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting iSDA layers: {str(e)}")
        return jsonify({'error': 'Failed to get layers data', 'details': str(e)}), 500

