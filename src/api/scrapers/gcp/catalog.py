import json
import os
from typing import Any, List

from api.db.query import insert_product
from api.db.types import Price, Product
from api.tools.hashing import generate_price_hash, generate_product_hash

from flask import current_app

import requests

base_url = 'https://cloudbilling.googleapis.com/v1'
gcp_api_key = os.environ.get('GCP_API_KEY')


class Sku(object):
    def __init__(self, name, skuId, description, category, serviceRegions, pricingInfo,
                 serviceProviderName, geoTaxonomy) -> None:
        self.name = name
        self.skuId = skuId
        self.description = description
        self.category = category
        self.serviceRegions = serviceRegions
        self.pricingInfo = pricingInfo
        self.serviceProviderName = serviceProviderName
        self.geoTaxonomy = geoTaxonomy


def get_service() -> List:
    """Query service information."""
    services = []
    next_page_token = ''

    # while next_page_token is not None:
    next_page_params = ''
    if next_page_token:
        next_page_params = f'&pageToken={next_page_token}'

    response = requests.get(
        f'{base_url}/services?key={gcp_api_key}{next_page_params}').json()
    services = response['services']
    next_page_token = response['nextPageToken']
    return services


def download_file():
    """Download pricing information file from a provider API."""
    services = get_service()
    for service in services:
        try:
            if service['name'] == 'services/6F81-5844-456A':  # Only scrapping for VMs
                download_service(service)
        except Exception as e:
            current_app.logger.error(f'Skipping due to {e}')


def download_service(service: Any):
    """
    Download service information.

    :service (Any) Service name
    """
    current_app.logger.info(f'Downloading GCP {service["displayName"]} pricing...')
    next_page_token = ''
    page = 1

    while True:
        current_app.logger.info(f'Downloading GCP serivce '
                                f'{service["displayName"]} page {page}')
        next_page_params = ''
        if next_page_token != '':
            next_page_params = f'&pageToken={next_page_token}'

        try:
            response = requests.get(f'{base_url}/services/{service["serviceId"]}'
                                    f'/skus?key={gcp_api_key}{next_page_params}')
        except requests.exceptions.Timeout:
            current_app.logger.info('Too many requests')
        except requests.exceptions.TooManyRedirects:
            pass
        except requests.exceptions.RequestException as e:
            current_app.logger.error('This is really bad, here we go: ', e)

        file_name = f'gcp-{service["displayName"]}-{page}'
        file_name = file_name.replace('/', '-')
        file_name = file_name.replace('.', '-')

        with open(f'data/{file_name}.json', 'wb') as handle:
            handle.write(response.content)

        response_json = response.json()
        next_page_token = response_json['nextPageToken']
        page += 1
        if next_page_token == '':
            break


def process_file(file_name: str):
    """
    Extract product's information from a file and dump it into a database.

    :file_name (str) File name
    """
    current_app.logger.info(f'Processing {file_name}...')

    file = open(file_name,)
    data = json.load(file)
    skus = data['skus']
    products = []

    for sku in skus:
        for region in sku['serviceRegions']:
            product = mapped_product(sku, region)
            products.append(product)

    file.close()
    insert_product(products)


def load_file():
    """Iterate over downloaded files and process it."""
    current_app.logger.info('Loading GCP catalog...')
    for filename in os.listdir('data'):
        if filename.startswith('gcp-'):
            current_app.logger.info(f'Loading {filename}...')
            try:
                process_file('data/' + filename)
            except Exception as e:
                current_app.logger.error(f'Skipping {filename} due to {e}')


def mapped_product(product_raw: Any, region: str) -> Product:
    """
    Generate product properties based on the product raw information.

    :product_raw (Any) Product Raw JSON information
    :region (str) Product's region

    Return a mapped product
    """
    product = Product(
        productHash='',
        sku=product_raw['skuId'],
        vendorName='gcp',
        region=region,
        service=product_raw['category']['serviceDisplayName'],
        productFamily=product_raw['category']['resourceFamily'],
        attributes={
            'description': product_raw['description'],
            'resourceGroup': product_raw['category']['resourceGroup'],
        },
        prices=[]
    )
    product.productHash = generate_product_hash(product)
    product.prices = mapped_price(product, product_raw)

    return product


def mapped_price(product: Product, product_raw: Any) -> List:
    """
    Generate price properties based on the product.

    :product (Product) Product object
    :product_raw (Any) Product Raw JSON information

    Return an array of mapped price object
    """
    prices = []

    for pricing in product_raw['pricingInfo']:
        for i in range(0, len(pricing['pricingExpression']['tieredRates'])):
            tier_rate = pricing['pricingExpression']['tieredRates'][i]

            price = Price(
                priceHash='',
                purchaseOption=product_raw['category']['usageType'],
                unit=pricing['pricingExpression']['usageUnitDescription'],
                price=f'{tier_rate["unitPrice"]["units"]}'
                      f'.{tier_rate["unitPrice"]["nanos"]:09}',
                effectiveDateStart=pricing['effectiveTime'],
                startUsageAmount=tier_rate['startUsageAmount']
            )

            try:
                next_tier = pricing['pricingExpression']['tieredRates'][i + 1]
                price.endUsageAmount = next_tier['startUsageAmount']
            except IndexError:
                pass

            price.priceHash = generate_price_hash(product, price)
            prices.append(price)

    return prices
