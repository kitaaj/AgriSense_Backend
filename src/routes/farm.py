from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.farm import Farm
import traceback
from datetime import datetime

farm_bp = Blueprint('farm', __name__)

@farm_bp.route('/farms', methods=['GET'])
@jwt_required()
def get_user_farms():
    """Get all farms for the current user"""
    try:
        jwt_identity = get_jwt_identity()
        
        current_user_id = int(jwt_identity)
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        farms = Farm.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'farms': [farm.to_dict() for farm in farms],
            'total': len(farms)
        }), 200

        
    except Exception as e:
        print(f"Error in get_user_farms: {e}")
        return jsonify({'error': 'Failed to get farms', 'details': str(e)}), 500

@farm_bp.route('/farms', methods=['POST'])
@jwt_required()
def create_farm():
    """Create a new farm"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'latitude', 'longitude']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate coordinates
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            
            if not (-90 <= latitude <= 90):
                return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
            if not (-180 <= longitude <= 180):
                return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
                
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid latitude or longitude format'}), 400
        
        # Validate area if provided
        area = data.get('area')
        if area is not None:
            try:
                area = float(area)
                if area <= 0:
                    return jsonify({'error': 'Area must be positive'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid area format'}), 400
        
        # Create new farm
        farm = Farm()
        
        farm.user_id=current_user_id
        farm.name=data['name'].strip()
        farm.description=str(data.get('description', '')).strip()
        farm.latitude=latitude
        farm.longitude=longitude
        farm.area=area
        farm.crop_type=str(data.get('crop_type', '')).strip()
        
        
        db.session.add(farm)
        db.session.commit()
        
        return jsonify({
            'message': 'Farm created successfully',
            'farm': farm.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create farm', 'details': str(e)}), 500

@farm_bp.route('/farms/<int:farm_id>', methods=['GET'])
@jwt_required()
def get_farm(farm_id):
    """Get a specific farm by ID"""
    try:
        current_user_id = int(get_jwt_identity())
        
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        return jsonify({
            'farm': farm.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get farm', 'details': str(e)}), 500

@farm_bp.route('/farms/<int:farm_id>', methods=['PUT'])
@jwt_required()
def update_farm(farm_id):
    """Update a farm"""
    try:
        current_user_id = int(get_jwt_identity())
        
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            farm.name = data['name'].strip()
        
        if 'description' in data:
            farm.description = data['description'].strip()
        
        if 'latitude' in data:
            try:
                latitude = float(data['latitude'])
                if not (-90 <= latitude <= 90):
                    return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
                farm.latitude = latitude
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid latitude format'}), 400
        
        if 'longitude' in data:
            try:
                longitude = float(data['longitude'])
                if not (-180 <= longitude <= 180):
                    return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
                farm.longitude = longitude
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid longitude format'}), 400
        
        if 'area' in data:
            if data['area'] is not None:
                try:
                    area = float(data['area'])
                    if area <= 0:
                        return jsonify({'error': 'Area must be positive'}), 400
                    farm.area = area
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid area format'}), 400
            else:
                farm.area = None
        
        if 'crop_type' in data:
            farm.crop_type = data['crop_type'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Farm updated successfully',
            'farm': farm.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update farm', 'details': str(e)}), 500

@farm_bp.route('/farms/<int:farm_id>', methods=['DELETE'])
@jwt_required()
def delete_farm(farm_id):
    """Delete a farm"""
    try:
        current_user_id = int(get_jwt_identity())
        
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        db.session.delete(farm)
        db.session.commit()
        
        return jsonify({
            'message': 'Farm deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete farm', 'details': str(e)}), 500

@farm_bp.route('/farms/<int:farm_id>/stats', methods=['GET'])
@jwt_required()
def get_farm_stats(farm_id):
    """Get statistics for a specific farm"""
    try:
        current_user_id = int(get_jwt_identity())
        
        farm = Farm.query.filter_by(id=farm_id, user_id=current_user_id).first()
        
        if not farm:
            return jsonify({'error': 'Farm not found'}), 404
        
        # Get soil analysis count
        from src.models.soil_analysis import SoilAnalysis
        soil_analysis_count = SoilAnalysis.query.filter_by(farm_id=farm_id).count()
        
        # Get latest soil analysis
        latest_analysis = SoilAnalysis.query.filter_by(farm_id=farm_id)\
            .order_by(SoilAnalysis.analyzed_at.desc()).first()
        
        stats = {
            'farm_id': farm_id,
            'soil_analyses_count': soil_analysis_count,
            'latest_analysis_date': latest_analysis.analyzed_at.isoformat() if latest_analysis else None,
            'farm_area': farm.area,
            'crop_type': farm.crop_type
        }
        
        return jsonify({
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get farm stats', 'details': str(e)}), 500

