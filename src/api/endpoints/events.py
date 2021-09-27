from flask import Blueprint, abort, jsonify, make_response
from api.scrapers.azure import retail
from api.db import setup


api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/setupdb')
def setup_db():
    setup.create_table_product('pricing')
    return make_response(jsonify("Database initialized successfully"), 200)

@api_routes.route('/scrape')
def scrape():
    return make_response(jsonify("successfully"), 200)

@api_routes.route('/dump')
def dump():
    return make_response(jsonify("successfully"), 200)

@api_routes.route('/load')
def load():
    try:
        setup.create_table_product('pricing')
        retail.load_file()
        return make_response(jsonify("successfully"), 200)
    except Exception:
        return make_response(jsonify("failed"), 400)

@api_routes.route('/download')
def download():
    retail.download_file()
    return make_response(jsonify("File downloaded successfully"), 200)

@api_routes.route('/query')
def query():
    return make_response(jsonify("File downloaded successfully"), 200)

@api_routes.route('/test')
def test():
    # setup.create_table_product('pricing')
    retail.load_file()
    print('Hi')
    return make_response(jsonify("successfully"), 200)
