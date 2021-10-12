from flask import Blueprint, jsonify, make_response, request
# from api.scrapers import aws
from api.scrapers.azure import retail
from api.scrapers.aws import awsBulk
from api.db import setup
from api.db.query import find_product
import json


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
        awsBulk.load_file()
        return make_response(jsonify("File loaded successfully"), 200)
    except Exception:
        return make_response(jsonify("Loading files failed"), 400)


@api_routes.route('/download')
def download():
    retail.download_file()
    awsBulk.download_file()
    return make_response(jsonify("File downloaded successfully"), 200)


@api_routes.route('/query', methods=['POST'])
def query():
    config = request.form or request.get_json()
    filter = config['filter']
    filter_parsed = json.loads(filter)
    attribute_filter = filter_parsed.pop('attributeFilters')
    products = find_product(filter_parsed, attribute_filter)
    responses = []

    if filter_parsed['vendorName'] == 'azure':
        purchase_option = config['purchase_option']
        if purchase_option == 'OnDemand':
            purchase_option = 'Consumption'
        for product in products:
            product_prices = product.prices
            first_key_price = list(product_prices.keys())[0]
            lastest_price = product_prices[first_key_price][0]
            if lastest_price['purchaseOption'] == purchase_option:
                response = {}
                response['price'] = lastest_price
                responses.append(response)
    elif filter_parsed['vendorName'] == 'aws':
        purchase_option = config['purchase_option']
        if purchase_option == 'OnDemand':
            purchase_option = 'on_demand'
        elif purchase_option == 'Reserved':
            purchase_option = 'reserved'
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
                response['price'] = lastest_price
                responses.append(response)

    return make_response(jsonify(responses), 200)


@api_routes.route('/health')
def vibe_check():
    return make_response(jsonify("Alive"), 200)
