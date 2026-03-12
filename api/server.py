from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError

# Initialize Flask application
app = Flask(__name__)

# Enable CORS
CORS(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
jwt = JWTManager(app)

# Initialize Rate Limiter
limiter = Limiter(app, key_func=get_remote_address)

# Request Validation Schema
class UserSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

# Error handling
@app.errorhandler(ValidationError)
def handle_validation_error(err):
    return {'message': err.messages}, 400

# Sample protected route
@app.route('/api/protected', methods=['GET'])
@jwt.required
@limiter.limit("5 per minute")
def protected_endpoint():
    return {'message': 'This is a protected route'}

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)