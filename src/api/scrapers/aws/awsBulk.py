import json
import os
from dataclasses import dataclass
from typing import Any, List

from api.db.query import insert_product
from api.db.types import Price, Product
from api.tools.hashing import generate_price_hash, generate_product_hash

from flask import current_app

import requests


@dataclass
class ProductRaw():
    sku: str
    productFamily: str
    attributes: Any


@dataclass
class PriceRaw():
    effectiveDate: str
    priceDimensions: Any
    termAttributes: Any


base_pricing_url = 'https://pricing.us-east-1.amazonaws.com'
index_url = '/offers/v1.0/aws/index.json'


def download_file():
    """Download pricing information file from a provider API."""
    current_app.logger.info('Downloading AWS Pricing API...')
    response = requests.get(base_pricing_url + index_url)

    response_json = response.json()
    for offer in response_json['offers']:
        download_service(response_json['offers'][offer])


def download_service(offer: str):
    """Download service information."""
    if offer['offerCode'] == 'AmazonEC2':
        response = requests.get(base_pricing_url + offer['currentRegionIndexUrl'])
        response_json = response.json()
        for region in response_json['regions']:
            current_app.logger.info(f'Download service from the region '
                                    f'{response_json["regions"][region]["regionCode"]}..')
            region_response = requests.get(base_pricing_url + response_json['regions']
                                           [region]['currentVersionUrl'])
            with open(f'data/aws-{offer["offerCode"]}-'
                      f'{response_json["regions"][region]["regionCode"]}'
                      f'.json', 'wb') as handle:
                handle.write(region_response.content)


def load_file():
    """Iterate over downloaded files and process it."""
    current_app.logger.info('Loading AWS pricing...')
    for filename in os.listdir('data'):
        if filename.startswith('aws-'):
            current_app.logger.info(f'Loading {filename}...')
            try:
                process_file('data/' + filename)
            except Exception as e:
                current_app.logger.error(f'Skipping {filename} due to {e}')


def process_file(file_name: str):
    """
    Extract product's information from a file and dump it into a database.

    :file_name (str) File name
    """
    current_app.logger.info(f'Processing {file_name}...')

    file = open(file_name,)
    data = json.load(file)

    products = map(lambda x: (mapped_product(data, ProductRaw(**x))),
                   data['products'].values())
    file.close()
    insert_product(products)


def mapped_product(data: Any, product_raw: ProductRaw) -> Product:
    """
    Generate product properties based on the product raw information.

    :product_raw (ProductRaw) Product Raw JSON information
    :data (Any) JSON response

    Return a mapped product
    """
    product = Product(
        productHash='',
        vendorName='aws',
        service=product_raw.attributes['servicecode'],
        productFamily=product_raw.productFamily,
        region=product_raw.attributes['location']
        if 'location' in product_raw.attributes else None,
        sku=product_raw.sku,
        attributes=product_raw.attributes,
        prices=[]
    )
    product.productHash = generate_product_hash(product)

    # print(data['terms'].keys())

    if 'OnDemand' in data['terms'] and product.sku in data['terms']['OnDemand']:
        product.prices = mapped_price(product,
                                      data['terms']['OnDemand'][product.sku],
                                      'on_demand')

    if 'Reserved' in data['terms'] and product.sku in data['terms']['Reserved']:
        product.prices = mapped_price(product,
                                      data['terms']['Reserved'][product.sku],
                                      'reserved')

    return product


def mapped_price(product: Product, price_raw: Any, purchase_option: str) -> List:
    """
    Generate price properties based on the product and the purchase option.

    :product (Product) Product object
    :price_raw (Any) Price object of a product
    :purchase_option (str) Purchase option

    Return an array of mapped price object
    """
    prices = []
    for price_item in price_raw.values():
        for price_dimension in price_item['priceDimensions'].values():
            prices = []
            price = Price(
                priceHash='',
                purchaseOption=purchase_option,
                unit=price_dimension['unit'],
                effectiveDateStart=price_item['effectiveDate'],
                startUsageAmount=price_dimension['beginRange']
                if 'beginRange' in price_dimension else '',
                endUsageAmount=price_dimension['endRange']
                if 'endRange' in price_dimension else '',
                description=price_dimension['description'],
                price=float(price_dimension['pricePerUnit']['USD'])
            )

            if purchase_option == 'reserved':
                if 'termAttributes' in price_dimension and \
                    'LeaseContractLength' in \
                        price_dimension['termAttributes']['LeaseContractLength']:
                    price.termLength = \
                        price_dimension['termAttributes']['LeaseContractLength']
                if 'termAttributes' in price_dimension and \
                    'LeaseContractLength' in \
                        price_dimension['termAttributes']['PurchaseOption']:
                    price.termPurchaseOption = \
                        price_dimension['termAttributes']['PurchaseOption']
                if 'termAttributes' in price_dimension and \
                    'LeaseContractLength' in \
                        price_dimension['termAttributes']['OfferingClass']:
                    price.termOfferingClass = \
                        price_dimension['termAttributes']['OfferingClass']

            price.priceHash = generate_price_hash(product, price)
            prices.append(price)

    return prices
