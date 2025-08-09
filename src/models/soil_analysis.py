from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
import json

class SoilAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.String(10), nullable=False)  # e.g., "0-20", "20-50"
    soil_properties = db.Column(db.JSON, nullable=False)  # Store all iSDA API response data
    analyzed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Farm
    farm = db.relationship('Farm', backref=db.backref('soil_analyses', lazy=True))

    def __repr__(self):
        return f'<SoilAnalysis {self.id} for Farm {self.farm_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'depth': self.depth,
            'soil_properties': self.soil_properties,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soil_analysis_id = db.Column(db.Integer, db.ForeignKey('soil_analysis.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # fertilizer, amendment, practice
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    dosage = db.Column(db.String(100))
    timing = db.Column(db.String(100))
    priority = db.Column(db.Integer, default=3)  # 1-5 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with SoilAnalysis
    soil_analysis = db.relationship('SoilAnalysis', backref=db.backref('recommendations', lazy=True))

    def __repr__(self):
        return f'<Recommendation {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'soil_analysis_id': self.soil_analysis_id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'dosage': self.dosage,
            'timing': self.timing,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

