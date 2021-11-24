import json
import re

# from api.scrapers import aws

from api.db import setup
from api.db.query import find_product
from api.scrapers.aws import awsBulk
from api.scrapers.azure import retail
from api.scrapers.gcp import catalog, machine

from flask import Blueprint, jsonify, make_response, request
from flask import current_app

api_routes = Blueprint('api_routes', __name__)


@api_routes.route('/setupdb')
def setup_db():
    setup.create_table_product('pricing')
    return make_response(jsonify('Database initialized successfully'), 200)


@api_routes.route('/load')
def load():
    is_ok = True

    try:
        setup.create_table_product('pricing')
    except Exception:
        is_ok = False
        current_app.logger.info('Setting up database failed')

    try:
        retail.load_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Loading Azure files failed')

    try:
        awsBulk.load_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Loading AWS files failed')

    try:
        catalog.load_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Loading GCP catalog files failed')

    try:
        machine.load_machine()
    except Exception:
        is_ok = False
        current_app.logger.info('Loading GCP machines failed')

    if is_ok:
        return make_response(jsonify('Files loaded successfully'), 200)
    else:
        return make_response(jsonify('Some of the file loading process has been failed, '
                                     'please check the log'), 400)


@api_routes.route('/download')
def download():
    is_ok = True

    try:
        retail.download_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Downloading Azure files failed')

    try:
        retail.scrape_size()
    except Exception:
        is_ok = False
        current_app.logger.info('Downloading Azure VM Size failed')

    try:
        awsBulk.download_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Downloading AWS files failed')

    try:
        catalog.download_file()
    except Exception:
        is_ok = False
        current_app.logger.info('Downloading GCP files failed')

    if is_ok:
        return make_response(jsonify('File downloaded successfully'), 200)
    else:
        return make_response(jsonify('Some of the downloading process has been failed, '
                                     'please check the log'), 400)


@api_routes.route('/query', methods=['POST'])
def query():
    config = request.form
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
        for price_val in product_prices.values():
            latest_price = price_val[0]
            if latest_price['purchaseOption'] == purchase_option:
                vcpu = product.attributes['vcpu']
                memory = product.attributes['memory']
                if (vcpu and type(vcpu) is str):
                    vcpu = float(re.sub("[^0-9.,]", '', vcpu))
                if (memory and type(memory) is str):
                    memory = float(re.sub("[^0-9.,]", '', memory))

                response = {
                    'cpu': vcpu,
                    'memory': memory,
                    'price': latest_price['price']
                }
                responses.append(response)

    return make_response(jsonify(responses), 200)


@api_routes.route('/health')
def vibe_check():
    return make_response(jsonify("Alive"), 200)
