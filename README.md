# AgriSense API Documentation

## Overview

AgriSense is a comprehensive soil analysis and farming recommendations API designed specifically for farmers in sub-Saharan Africa. The API integrates with the iSDA (Innovative Solutions for Decision Agriculture) soil data service to provide accurate soil analysis and generate personalized farming recommendations.

### Key Features

- **User Authentication & Management**: Secure JWT-based authentication system
- **Farm Management**: Create, update, and manage multiple farm locations
- **Soil Analysis**: Integration with iSDA API for comprehensive soil property analysis
- **Smart Recommendations**: AI-powered farming recommendations based on soil conditions
- **Soil Health Scoring**: Comprehensive soil health assessment and scoring
- **Dashboard Analytics**: User-friendly dashboard with statistics and insights

### Technology Stack

- **Backend Framework**: Flask (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT (JSON Web Tokens)
- **External API**: iSDA Africa Soil Data API
- **CORS**: Enabled for cross-origin requests

## Base URL

```
Development: http://localhost:5000
Production: https://your-domain.com
```

## Authentication

AgriSense uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header for protected endpoints:

```
Authorization: Bearer <your_jwt_token>
```

### Token Expiration
- Access tokens expire after 24 hours
- Refresh tokens expire after 30 days
- Use the refresh endpoint to get new access tokens

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string (required)",
  "email": "string (required)",
  "password": "string (required, min 6 chars)",
  "full_name": "string (optional)",
  "phone_number": "string (optional)"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Test Farmer",
    "phone_number": "+254700000000",
    "is_active": true,
    "created_at": "2025-08-08T16:33:04.953156",
    "updated_at": "2025-08-08T16:33:04.953160"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### POST /api/auth/login
Authenticate user and get access tokens.

**Request Body:**
```json
{
  "username": "string (required - username or email)",
  "password": "string (required)"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Test Farmer",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### GET /api/auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Test Farmer",
    "phone_number": "+254700000000",
    "is_active": true,
    "created_at": "2025-08-08T16:33:04.953156",
    "updated_at": "2025-08-08T16:33:04.953160"
  }
}
```

#### POST /api/auth/logout
Logout user (invalidate token).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Logout successful"
}
```




### Farm Management Endpoints

#### GET /api/farms
Get all farms for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "farms": [
    {
      "id": 1,
      "user_id": 1,
      "name": "Greenfield Farm",
      "description": "Main corn production farm",
      "latitude": -1.2921,
      "longitude": 36.8219,
      "area": 120.5,
      "crop_type": "Corn",
      "created_at": "2025-08-08T16:35:33.349726",
      "updated_at": "2025-08-08T16:35:33.349733"
    }
  ],
  "total": 1
}
```

#### POST /api/farms
Create a new farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "latitude": "number (required, -90 to 90)",
  "longitude": "number (required, -180 to 180)",
  "area": "number (optional, hectares)",
  "crop_type": "string (optional)"
}
```

**Response (201):**
```json
{
  "message": "Farm created successfully",
  "farm": {
    "id": 1,
    "user_id": 1,
    "name": "Greenfield Farm",
    "description": "Main corn production farm",
    "latitude": -1.2921,
    "longitude": 36.8219,
    "area": 120.5,
    "crop_type": "Corn",
    "created_at": "2025-08-08T16:35:33.349726",
    "updated_at": "2025-08-08T16:35:33.349733"
  }
}
```

#### GET /api/farms/{farm_id}
Get a specific farm by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "farm": {
    "id": 1,
    "user_id": 1,
    "name": "Greenfield Farm",
    "description": "Main corn production farm",
    "latitude": -1.2921,
    "longitude": 36.8219,
    "area": 120.5,
    "crop_type": "Corn",
    "created_at": "2025-08-08T16:35:33.349726",
    "updated_at": "2025-08-08T16:35:33.349733"
  }
}
```

#### PUT /api/farms/{farm_id}
Update a farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "latitude": "number (optional)",
  "longitude": "number (optional)",
  "area": "number (optional)",
  "crop_type": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Farm updated successfully",
  "farm": {
    "id": 1,
    "name": "Updated Farm Name",
    "description": "Updated description",
    "latitude": -1.2921,
    "longitude": 36.8219,
    "area": 150.0,
    "crop_type": "Maize",
    "updated_at": "2025-08-08T17:00:00.000000"
  }
}
```

#### DELETE /api/farms/{farm_id}
Delete a farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Farm deleted successfully"
}
```

#### GET /api/farms/{farm_id}/stats
Get statistics for a specific farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "stats": {
    "farm_id": 1,
    "soil_analyses_count": 3,
    "latest_analysis_date": "2025-08-08T16:45:00.000000",
    "farm_area": 120.5,
    "crop_type": "Corn"
  }
}
```


### Soil Analysis Endpoints

#### POST /api/farms/{farm_id}/soil-analysis
Perform soil analysis for a farm using iSDA API.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "latitude": "number (optional, uses farm coordinates if not provided)",
  "longitude": "number (optional, uses farm coordinates if not provided)",
  "depth": "string (optional, default: '0-20')"
}
```

**Response (201):**
```json
{
  "message": "Soil analysis completed successfully",
  "analysis": {
    "id": 1,
    "farm_id": 1,
    "latitude": -1.2921,
    "longitude": 36.8219,
    "depth": "0-20",
    "soil_properties": {
      "ph": [
        {
          "value": {"value": 6.5},
          "uncertainty": [
            {"type": "standard_error", "value": 0.1},
            {"lower_bound": 6.3, "upper_bound": 6.7}
          ]
        }
      ],
      "carbon_organic": [
        {
          "value": {"value": 1.9},
          "uncertainty": [
            {"type": "standard_error", "value": 0.2},
            {"lower_bound": 1.7, "upper_bound": 2.1}
          ]
        }
      ]
    },
    "analyzed_at": "2025-08-08T16:45:00.000000",
    "created_at": "2025-08-08T16:45:00.000000"
  },
  "recommendations": [
    {
      "id": 1,
      "soil_analysis_id": 1,
      "type": "fertilizer",
      "title": "Apply Nitrogen Fertilizer",
      "description": "Total nitrogen is 0.12%, which is low. Apply nitrogen fertilizer to support crop growth.",
      "dosage": "100-150 kg N per hectare",
      "timing": "Split application: 1/3 at planting, 2/3 at 6 weeks",
      "priority": 2,
      "created_at": "2025-08-08T16:45:00.000000"
    }
  ],
  "health_score": {
    "overall_score": 72.5,
    "health_category": "Good",
    "property_scores": {
      "ph": 95.0,
      "carbon_organic": 85.0,
      "nitrogen_total": 45.0,
      "phosphorous_extractable": 60.0,
      "potassium_extractable": 75.0
    },
    "analyzed_at": "2025-08-08T16:45:00.000000"
  }
}
```

#### GET /api/farms/{farm_id}/soil-analyses
Get all soil analyses for a farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit`: Number of results to return (default: 10)
- `offset`: Number of results to skip (default: 0)

**Response (200):**
```json
{
  "analyses": [
    {
      "id": 1,
      "farm_id": 1,
      "latitude": -1.2921,
      "longitude": 36.8219,
      "depth": "0-20",
      "soil_properties": {...},
      "analyzed_at": "2025-08-08T16:45:00.000000",
      "created_at": "2025-08-08T16:45:00.000000"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/soil-analyses/{analysis_id}
Get a specific soil analysis with recommendations.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "analysis": {
    "id": 1,
    "farm_id": 1,
    "latitude": -1.2921,
    "longitude": 36.8219,
    "depth": "0-20",
    "soil_properties": {...},
    "analyzed_at": "2025-08-08T16:45:00.000000"
  },
  "recommendations": [
    {
      "id": 1,
      "type": "fertilizer",
      "title": "Apply Nitrogen Fertilizer",
      "description": "Total nitrogen is 0.12%, which is low...",
      "dosage": "100-150 kg N per hectare",
      "timing": "Split application: 1/3 at planting, 2/3 at 6 weeks",
      "priority": 2
    }
  ],
  "health_score": {
    "overall_score": 72.5,
    "health_category": "Good",
    "property_scores": {...}
  }
}
```

#### GET /api/soil-analyses/{analysis_id}/recommendations
Get recommendations for a specific soil analysis.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "recommendations": [
    {
      "id": 1,
      "soil_analysis_id": 1,
      "type": "fertilizer",
      "title": "Apply Nitrogen Fertilizer",
      "description": "Total nitrogen is 0.12%, which is low. Apply nitrogen fertilizer to support crop growth.",
      "dosage": "100-150 kg N per hectare",
      "timing": "Split application: 1/3 at planting, 2/3 at 6 weeks",
      "priority": 2,
      "created_at": "2025-08-08T16:45:00.000000"
    }
  ],
  "analysis_id": 1,
  "total": 1
}
```

#### GET /api/farms/{farm_id}/soil-health-summary
Get soil health summary for a farm.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "farm_id": 1,
  "has_analysis": true,
  "latest_analysis_date": "2025-08-08T16:45:00.000000",
  "health_score": {
    "overall_score": 72.5,
    "health_category": "Good",
    "property_scores": {...}
  },
  "high_priority_recommendations": 2,
  "total_analyses": 3
}
```

#### GET /api/isda/layers
Get available soil property layers from iSDA API.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "layers": {
    "depths": ["0-20", "20-50", "0-50", "0-200"],
    "properties": [
      {
        "name": "ph",
        "description": "Soil pH",
        "unit": "pH",
        "depths": ["0-20", "20-50"]
      },
      {
        "name": "carbon_organic",
        "description": "Organic Carbon",
        "unit": "%",
        "depths": ["0-20", "20-50"]
      }
    ]
  },
  "message": "Available soil property layers retrieved successfully"
}
```


### Utility Endpoints

#### GET /api/dashboard
Get dashboard data for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Test Farmer"
  },
  "stats": {
    "farms_count": 3,
    "total_analyses": 8,
    "high_priority_recommendations": 5,
    "average_soil_health": 68.5
  },
  "recent_analyses": [
    {
      "id": 3,
      "farm_id": 1,
      "farm_name": "Greenfield Farm",
      "analyzed_at": "2025-08-08T16:45:00.000000",
      "depth": "0-20"
    }
  ]
}
```

#### GET /api/search
Search across farms and analyses for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `q`: Search query (required, min 2 characters)

**Response (200):**
```json
{
  "farms": [
    {
      "id": 1,
      "name": "Greenfield Farm",
      "description": "Main corn production farm",
      "crop_type": "Corn",
      "latitude": -1.2921,
      "longitude": 36.8219
    }
  ],
  "total_results": 1,
  "query": "corn"
}
```

#### GET /api/profile
Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "profile": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Test Farmer",
    "phone_number": "+254700000000",
    "is_active": true,
    "created_at": "2025-08-08T16:33:04.953156",
    "updated_at": "2025-08-08T16:33:04.953160",
    "stats": {
      "farms_count": 3,
      "analyses_count": 8,
      "member_since": "August 2025"
    }
  }
}
```

#### PUT /api/profile
Update current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "full_name": "string (optional)",
  "phone_number": "string (optional)",
  "email": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "id": 1,
    "username": "testfarmer",
    "email": "farmer@test.com",
    "full_name": "Updated Name",
    "phone_number": "+254700000001",
    "updated_at": "2025-08-08T17:00:00.000000"
  }
}
```

#### POST /api/change-password
Change user password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 6 chars)"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

#### GET /api/app-info
Get application information (public endpoint).

**Response (200):**
```json
{
  "app_name": "AgriSense API",
  "version": "1.0.0",
  "description": "Soil analysis and farming recommendations API for sub-Saharan Africa",
  "features": [
    "User authentication and management",
    "Farm management",
    "Soil analysis using iSDA data",
    "Personalized farming recommendations",
    "Soil health scoring"
  ],
  "endpoints": {
    "authentication": "/api/auth/*",
    "farms": "/api/farms/*",
    "soil_analysis": "/api/farms/*/soil-analysis",
    "dashboard": "/api/dashboard",
    "health": "/api/health"
  }
}
```

#### GET /api/statistics
Get detailed statistics for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `days`: Number of days for recent statistics (default: 30)

**Response (200):**
```json
{
  "statistics": {
    "period_days": 30,
    "farms": {
      "total": 3,
      "crop_distribution": [
        {"crop_type": "Corn", "count": 2},
        {"crop_type": "Soybeans", "count": 1}
      ]
    },
    "analyses": {
      "total": 8,
      "recent": 3
    },
    "recommendations": {
      "total": 24,
      "high_priority": 5
    }
  }
}
```

#### GET /api/health
Health check endpoint (public).

**Response (200):**
```json
{
  "status": "healthy",
  "service": "AgriSense API"
}
```

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses:

### Error Response Format

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: External service unavailable

### Authentication Errors

```json
{
  "error": "Authentication Error",
  "message": "Invalid or expired authentication token",
  "status_code": 401
}
```

### Validation Errors

```json
{
  "error": "Bad Request",
  "message": "Latitude must be between -90 and 90",
  "status_code": 400
}
```

### External Service Errors

```json
{
  "error": "Service Unavailable",
  "message": "Failed to authenticate with soil data service",
  "status_code": 503
}
```


### Services

#### iSDA Service
The `ISDAService` class handles integration with the iSDA Africa soil data API:

- **Authentication**: Manages JWT tokens for iSDA API access
- **Soil Data Retrieval**: Fetches comprehensive soil property data
- **Error Handling**: Robust error handling for API failures
- **Token Management**: Automatic token refresh when expired

#### Recommendation Service
The `RecommendationService` class generates farming recommendations:

- **Soil Analysis**: Analyzes soil properties against optimal ranges
- **Recommendation Generation**: Creates actionable farming recommendations
- **Health Scoring**: Calculates overall soil health scores
- **Priority Assignment**: Assigns priority levels to recommendations

### Security Features

#### Password Security
- Passwords are hashed using Werkzeug's secure password hashing
- Minimum password length requirement (6 characters)
- Password validation on registration and change

#### JWT Security
- Secure JWT token generation with configurable expiration
- Refresh token mechanism for extended sessions
- Token validation on all protected endpoints

#### Input Validation
- Comprehensive input validation for all endpoints
- Coordinate validation for geographic data
- Email format validation
- SQL injection prevention through ORM usage

#### CORS Configuration
- Cross-Origin Resource Sharing enabled for frontend integration
- Configurable origins for production security

### Middleware

#### Error Handling
- Centralized error handling for consistent responses
- HTTP status code mapping
- Detailed error logging for debugging
- User-friendly error messages

#### Request Logging
- Comprehensive request/response logging
- Performance monitoring with request timing
- Sensitive data filtering in logs
- Structured logging format

## Deployment Guide

### Prerequisites

1. **Python 3.11+**
2. **Virtual Environment**
3. **PostgreSQL** (for production)
4. **iSDA API Credentials**

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/agrisense

# iSDA API Configuration
ISDA_USERNAME=your-isda-username
ISDA_PASSWORD=your-isda-password

# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.com
```

### Installation Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd agrisense-backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up database:**
```bash
# For PostgreSQL
createdb agrisense
python -c "from src.main import app, db; app.app_context().push(); db.create_all()"
```

5. **Run the application:**
```bash
python src/main.py
```

### Production Deployment

#### Using Gunicorn

1. **Install Gunicorn:**
```bash
pip install gunicorn
```

2. **Create Gunicorn configuration:**
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

3. **Run with Gunicorn:**
```bash
gunicorn -c gunicorn.conf.py src.main:app
```

#### Using Docker

1. **Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.main:app"]
```

2. **Build and run:**
```bash
docker build -t agrisense-api .
docker run -p 5000:5000 --env-file .env agrisense-api
```

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring and Logging

#### Application Logging
- Configure logging levels for different environments
- Use structured logging for better analysis
- Implement log rotation to manage disk space

#### Health Monitoring
- Use the `/api/health` endpoint for health checks
- Monitor response times and error rates
- Set up alerts for service failures

#### Database Monitoring
- Monitor database connection pool
- Track query performance
- Set up database backups

### Performance Optimization

#### Database Optimization
- Add indexes for frequently queried fields
- Use database connection pooling
- Implement query optimization

#### Caching
- Implement Redis caching for frequently accessed data
- Cache iSDA API responses to reduce external calls
- Use HTTP caching headers for static responses

#### Rate Limiting
- Implement rate limiting to prevent abuse
- Use Redis for distributed rate limiting
- Configure different limits for different endpoints

## Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### API Tests
```bash
python -m pytest tests/api/
```

### Test Coverage
```bash
coverage run -m pytest
coverage report
coverage html
```

## API Client Examples

### Python Client Example

```python
import requests

class AgriSenseClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.access_token = None
        self.login(username, password)
    
    def login(self, username, password):
        response = requests.post(f"{self.base_url}/api/auth/login", json={
            "username": username,
            "password": password
        })
        data = response.json()
        self.access_token = data["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def create_farm(self, name, latitude, longitude, **kwargs):
        data = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            **kwargs
        }
        response = requests.post(
            f"{self.base_url}/api/farms",
            json=data,
            headers=self.get_headers()
        )
        return response.json()
    
    def analyze_soil(self, farm_id, **kwargs):
        response = requests.post(
            f"{self.base_url}/api/farms/{farm_id}/soil-analysis",
            json=kwargs,
            headers=self.get_headers()
        )
        return response.json()

# Usage
client = AgriSenseClient("http://localhost:5000", "username", "password")
farm = client.create_farm("Test Farm", -1.2921, 36.8219, crop_type="Corn")
analysis = client.analyze_soil(farm["farm"]["id"])
```

### JavaScript Client Example

```javascript
class AgriSenseClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.accessToken = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        this.accessToken = data.access_token;
        return data;
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`
        };
    }

    async createFarm(farmData) {
        const response = await fetch(`${this.baseUrl}/api/farms`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(farmData)
        });
        return response.json();
    }

    async analyzeSoil(farmId, analysisData = {}) {
        const response = await fetch(`${this.baseUrl}/api/farms/${farmId}/soil-analysis`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(analysisData)
        });
        return response.json();
    }

    async getDashboard() {
        const response = await fetch(`${this.baseUrl}/api/dashboard`, {
            headers: this.getHeaders()
        });
        return response.json();
    }
}

// Usage
const client = new AgriSenseClient('http://localhost:5000');
await client.login('username', 'password');
const farm = await client.createFarm({
    name: 'Test Farm',
    latitude: -1.2921,
    longitude: 36.8219,
    crop_type: 'Corn'
});
const analysis = await client.analyzeSoil(farm.farm.id);
```

## Support and Contributing

### Getting Help
- Check the API documentation for endpoint details
- Review error messages for troubleshooting guidance
- Use the health check endpoint to verify service status

### Contributing
- Follow the existing code style and patterns
- Add tests for new features
- Update documentation for API changes
- Submit pull requests with clear descriptions

### License
This project is licensed under the MIT License. See LICENSE file for details.

---

**AgriSense API v1.0.0** - Empowering farmers in sub-Saharan Africa with data-driven soil insights and recommendations.

