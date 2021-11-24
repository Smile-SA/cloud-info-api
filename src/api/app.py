import logging

from api.db.setup import setup_db
from api.endpoints.events import api_routes
from api.job import run_scheduler

from flask import Flask


def initialize_app():
    app = Flask(__name__)
    app.register_blueprint(api_routes)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@' \
                                            'cloud-pricing-postgresql-headless:5432/' \
                                            'postgres'
    app.config.from_object('src.api.config.ProductionConfig')
    configure_logging()
    return app


def configure_logging():
    # register root logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.INFO)


def create_app():
    """
    export FLASK_APP=api.app:create_app
    ./venv/bin/python -m flask run --host "${ipaddr}" --port 5042
    """
    app = initialize_app()
    setup_db(app)
    run_scheduler()
    return app
