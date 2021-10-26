import os
import requests
import json
from dataclasses import dataclass
from typing import Any
from flask import current_app

from api.db.types import Price, Product
from api.db.query import insert_product
from api.tools.hashing import generate_product_hash, generate_price_hash


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
    current_app.logger.info('Downloading AWS Pricing API...')
    response = requests.get(base_pricing_url + index_url)

    response_json = response.json()
    for offer in response_json['offers']:
        download_service(response_json['offers'][offer])


def download_service(offer):
    if offer['offerCode'] == 'AmazonEC2':
        response = requests.get(base_pricing_url + offer['currentRegionIndexUrl'])
        response_json = response.json()
        for region in response_json['regions']:
            if region == 'eu-west-3':
                region_response = requests.get(base_pricing_url + response_json['regions']
                                               [region]['currentVersionUrl'])
                with open(f"data/aws-{offer['offerCode']}-{response_json['regions'][region]['regionCode']}.json",
                          "wb") as handle:
                    handle.write(region_response.content)


def load_file():
    current_app.logger.info('Loading AWS pricing...')
    for filename in os.listdir('data'):
        if filename.startswith('aws-'):
            current_app.logger.info(f'Loading {filename}...')
            try:
                process_file('data/' + filename)
            except Exception as e:
                current_app.logger.error(f'Skipping {filename} due to {e}')


def process_file(file_name):
    current_app.logger.info(f'Processing {file_name}...')

    file = open(file_name,)
    data = json.load(file)

    products = map(lambda x: (mapped_product(data, ProductRaw(**x))),
                   data['products'].values())
    file.close()
    insert_product(products)


def mapped_product(data, product_raw: ProductRaw):
    product = Product(
        productHash='',
        vendorName='aws',
        service=product_raw.attributes['servicecode'],
        productFamily=product_raw.productFamily,
        region=product_raw.attributes['location'],
        sku=product_raw.sku,
        attributes=product_raw.attributes,
        prices=[]
    )
    product.productHash = generate_product_hash(product)

    if data['terms']['OnDemand'] and product.sku in data['terms']['OnDemand']:
        product.prices = mapped_price(product,
                                      data['terms']['OnDemand'][product.sku],
                                      'on_demand')

    if data['terms']['Reserved'] and product.sku in data['terms']['Reserved']:
        product.prices = mapped_price(product,
                                      data['terms']['Reserved'][product.sku],
                                      'reserved')

    return product


def mapped_price(product: Product, price_raw, purchase_option: str):
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
                price=price_dimension['pricePerUnit']['USD']
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
