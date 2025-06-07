from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from blueprints.auth import auth_bp
from blueprints.algorithms import algorithms_bp
from blueprints.visualization import visualization_bp

load_dotenv()
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(algorithms_bp, url_prefix='/api/algorithms')
    app.register_blueprint(visualization_bp, url_prefix='/api/visualization')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 