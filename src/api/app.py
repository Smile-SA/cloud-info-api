from flask import Flask

from api.endpoints.events import api_routes
from api.db.setup import setup_db

def initialize_app():
    app = Flask(__name__)
    app.register_blueprint(api_routes)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432' 
    return app

def create_app():
    """
    export FLASK_APP=api.cloud-pricing.app:create_app
    ./venv/bin/python -m flask run --host "${ipaddr}" --port 5042
    """
    app = initialize_app()
    setup_db(app)
    return app
