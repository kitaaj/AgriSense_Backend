from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.farm import Farm
from src.models.soil_analysis import SoilAnalysis, Recommendation
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

utils_bp = Blueprint('utils', __name__)

@utils_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get dashboard data for the current user"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's farms count
        farms_count = Farm.query.filter_by(user_id=current_user_id).count()
        
        # Get recent soil analyses
        recent_analyses = SoilAnalysis.query.join(Farm)\
            .filter(Farm.user_id == current_user_id)\
            .order_by(SoilAnalysis.analyzed_at.desc())\
            .limit(5).all()
        
        # Get high priority recommendations count
        high_priority_recs = Recommendation.query.join(SoilAnalysis).join(Farm)\
            .filter(Farm.user_id == current_user_id, Recommendation.priority <= 2)\
            .count()
        
        # Get total soil analyses count
        total_analyses = SoilAnalysis.query.join(Farm)\
            .filter(Farm.user_id == current_user_id).count()
        
        # Calculate average soil health score for user's farms
        avg_health_score = None
        if recent_analyses:
            from src.services.recommendation_service import recommendation_service
            scores = []
            for analysis in recent_analyses:
                health_data = recommendation_service.get_soil_health_score(analysis.soil_properties)
                if health_data.get('overall_score'):
                    scores.append(health_data['overall_score'])
            
            if scores:
                avg_health_score = sum(scores) / len(scores)
        
        dashboard_data = {
            'user': user.to_dict(),
            'stats': {
                'farms_count': farms_count,
                'total_analyses': total_analyses,
                'high_priority_recommendations': high_priority_recs,
                'average_soil_health': round(avg_health_score, 1) if avg_health_score else None
            },
            'recent_analyses': [
                {
                    'id': analysis.id,
                    'farm_id': analysis.farm_id,
                    'farm_name': analysis.farm.name,
                    'analyzed_at': analysis.analyzed_at.isoformat(),
                    'depth': analysis.depth
                } for analysis in recent_analyses
            ]
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data', 'details': str(e)}), 500

@utils_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    """Search across farms and analyses for the current user"""
    try:
        current_user_id = int(get_jwt_identity())
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        if len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400
        
        # Search farms
        farms = Farm.query.filter(
            Farm.user_id == current_user_id,
            Farm.name.ilike(f'%{query}%')
        ).limit(10).all()
        
        # Search by crop type
        crop_farms = Farm.query.filter(
            Farm.user_id == current_user_id,
            Farm.crop_type.ilike(f'%{query}%')
        ).limit(10).all()
        
        # Combine and deduplicate farms
        all_farms = {farm.id: farm for farm in farms + crop_farms}
        
        search_results = {
            'farms': [farm.to_dict() for farm in all_farms.values()],
            'total_results': len(all_farms),
            'query': query
        }
        
        return jsonify(search_results), 200
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@utils_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get additional profile stats
        farms_count = Farm.query.filter_by(user_id=current_user_id).count()
        analyses_count = SoilAnalysis.query.join(Farm)\
            .filter(Farm.user_id == current_user_id).count()
        
        profile_data = user.to_dict()
        profile_data['stats'] = {
            'farms_count': farms_count,
            'analyses_count': analyses_count,
            'member_since': user.created_at.strftime('%B %Y') if user.created_at else None
        }
        
        return jsonify({'profile': profile_data}), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@utils_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'].strip()
        
        if 'phone_number' in data:
            user.phone_number = data['phone_number'].strip()
        
        # Email update requires validation
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                # Check if email already exists
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    return jsonify({'error': 'Email already in use'}), 409
                user.email = new_email
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@utils_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        new_password = data['new_password']
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500

@utils_bp.route('/app-info', methods=['GET'])
def get_app_info():
    """Get application information (public endpoint)"""
    return jsonify({
        'app_name': 'AgriSense API',
        'version': '1.0.0',
        'description': 'Soil analysis and farming recommendations API for sub-Saharan Africa',
        'features': [
            'User authentication and management',
            'Farm management',
            'Soil analysis using iSDA data',
            'Personalized farming recommendations',
            'Soil health scoring'
        ],
        'endpoints': {
            'authentication': '/api/auth/*',
            'farms': '/api/farms/*',
            'soil_analysis': '/api/farms/*/soil-analysis',
            'dashboard': '/api/dashboard',
            'health': '/api/health'
        }
    }), 200

@utils_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_user_statistics():
    """Get detailed statistics for the current user"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get date range from query params (default to last 30 days)
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Farms statistics
        total_farms = Farm.query.filter_by(user_id=current_user_id).count()
        
        # Crop type distribution
        crop_stats = db.session.query(
            Farm.crop_type, 
            db.func.count(Farm.id).label('count')
        ).filter(
            Farm.user_id == current_user_id,
            Farm.crop_type.isnot(None),
            Farm.crop_type != ''
        ).group_by(Farm.crop_type).all()
        
        # Soil analyses statistics
        total_analyses = SoilAnalysis.query.join(Farm)\
            .filter(Farm.user_id == current_user_id).count()
        
        recent_analyses = SoilAnalysis.query.join(Farm)\
            .filter(
                Farm.user_id == current_user_id,
                SoilAnalysis.analyzed_at >= start_date
            ).count()
        
        # Recommendations statistics
        total_recommendations = Recommendation.query.join(SoilAnalysis).join(Farm)\
            .filter(Farm.user_id == current_user_id).count()
        
        high_priority_recs = Recommendation.query.join(SoilAnalysis).join(Farm)\
            .filter(
                Farm.user_id == current_user_id,
                Recommendation.priority <= 2
            ).count()
        
        statistics = {
            'period_days': days,
            'farms': {
                'total': total_farms,
                'crop_distribution': [
                    {'crop_type': crop, 'count': count} 
                    for crop, count in crop_stats
                ]
            },
            'analyses': {
                'total': total_analyses,
                'recent': recent_analyses
            },
            'recommendations': {
                'total': total_recommendations,
                'high_priority': high_priority_recs
            }
        }
        
        return jsonify({'statistics': statistics}), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'error': 'Failed to get statistics', 'details': str(e)}), 500

