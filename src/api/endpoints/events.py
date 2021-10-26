from flask import Blueprint, jsonify, make_response, request
# from api.scrapers import aws
from api.scrapers.azure import retail
from api.scrapers.aws import awsBulk
from api.scrapers.gcp import catalog, machine
from api.db import setup
from flask import current_app
from api.db.query import find_product
import json

api_routes = Blueprint('api_routes', __name__)


@api_routes.route('/setupdb')
def setup_db():
    setup.create_table_product('pricing')
    return make_response(jsonify("Database initialized successfully"), 200)


@api_routes.route('/load')
def load():
    try:
        setup.create_table_product('pricing')
        retail.load_file()
        awsBulk.load_file()
        catalog.load_file()
        machine.load_machine()
        return make_response(jsonify("File loaded successfully"), 200)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify("Loading files failed"), 400)


@api_routes.route('/download')
def download():
    try:
        retail.download_file()
        awsBulk.download_file()
        catalog.download_file()
        return make_response(jsonify("File downloaded successfully"), 200)
    except Exception:
        return make_response(jsonify("Downloading files failed"), 400)


@api_routes.route('/query', methods=['POST'])
def query():
    config = request.form or request.get_json()
    filter = config['filter']
    filter_parsed = json.loads(filter)
    attribute_filter = filter_parsed.pop('attributeFilters')
    products = find_product(filter_parsed, attribute_filter)
    responses = []

    purchase_option = config['purchase_option']
    purchase_option = {
        ('aws', 'OnDemand'): 'on_demand',
        ('aws', 'Reserved'): 'reserved',
        ('aws', 'Spot'): 'spot',
        ('azure', 'OnDemand'): 'Consumption',
        ('azure', 'Reserved'): 'Reservation',
        ('azure', 'Spot'): 'Spot',
        ('gcp', 'OnDemand'): 'on_demand',
        ('gcp', 'Reserved'): 'reserved',
        ('gcp', 'Spot'): 'preemptible',
    }[filter_parsed['vendorName'], purchase_option]

    for product in products:
        product_prices = product.prices
        first_key_price = list(product_prices.keys())[0]
        lastest_price = product_prices[first_key_price][0]
        if lastest_price['purchaseOption'] == purchase_option:
            vcpu = product.attributes['vcpu']
            memory = product.attributes['memory']
            response = {}
            response['vcpu'] = vcpu
            response['memory'] = memory
            response['price'] = lastest_price['price']
            responses.append(response)

    return make_response(jsonify(responses), 200)


@api_routes.route('/health')
def vibe_check():
    return make_response(jsonify("Alive"), 200)
