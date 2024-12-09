from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
import openai
from models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database setup
engine = create_engine('sqlite:///llc_formation.db')
Session = sessionmaker(bind=engine)
session = Session()

# Create admin user if it doesn't exist
def create_admin_user():
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@alfa.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # Change this in production
    
    admin = session.query(User).filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            name='ALFA Admin',
            role='admin'
        )
        admin.set_password(admin_password)
        session.add(admin)
        session.commit()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401
    
    user = session.query(User).filter_by(email=auth.get('email')).first()
    
    if not user or not user.check_password(auth.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    session.commit()
    
    token = jwt.encode({
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    existing_user = session.query(User).filter_by(email=data.get('email')).first()
    if existing_user:
        return jsonify({'message': 'Email already registered'}), 400
    
    new_user = User(
        email=data.get('email'),
        name=data.get('name'),
        role='user'  # Default role is user
    )
    new_user.set_password(data.get('password'))
    
    session.add(new_user)
    session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/llc/formation/start', methods=['POST'])
@token_required
def start_llc_formation():
    data = request.json
    # Initial LLC formation data validation and processing
    return jsonify({
        'status': 'success',
        'message': 'LLC formation process initiated',
        'data': {
            'formationId': 'LLC-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'state': data.get('state'),
            'companyName': data.get('companyName')
        }
    })

@app.route('/api/business/insights', methods=['POST'])
@token_required
def get_business_insights():
    data = request.json
    try:
        # Generate business insights using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Adam, an expert business advisor."},
                {"role": "user", "content": f"Provide strategic insights for a {data.get('industry')} business in {data.get('state')}"}
            ]
        )
        insights = response.choices[0].message.content
        
        return jsonify({
            'status': 'success',
            'insights': insights
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/documents/generate', methods=['POST'])
@token_required
def generate_documents():
    data = request.json
    document_type = data.get('documentType')
    
    # Template generation logic would go here
    templates = {
        'operating_agreement': 'Operating Agreement template content...',
        'articles_of_organization': 'Articles of Organization template content...'
    }
    
    return jsonify({
        'status': 'success',
        'document': {
            'type': document_type,
            'content': templates.get(document_type, 'Template not found'),
            'generated_at': datetime.now().isoformat()
        }
    })

if __name__ == '__main__':
    create_admin_user()  # Create admin user on startup
    app.run(debug=True)
