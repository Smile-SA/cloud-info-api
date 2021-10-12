import os
from typing import Any
import requests
import logging
import json
from dataclasses import dataclass

from api.db.query import insert_product
from api.db.types import Price, Product
from api.tools.hashing import generate_product_hash, generate_price_hash


# basePricingURL = 'https://prices.azure.com/api/retail/prices'
basePricingURL = """https://prices.azure.com/api/retail/prices?$filter=serviceName eq \
    'Virtual Machines' and armRegionName eq 'westeurope'"""
logging.basicConfig(level=logging.INFO)


@dataclass
class ProductRaw():
    currencyCode: str
    tierMinimumUnits: str
    retailPrice: str
    unitPrice: str
    armRegionName: str
    location: str
    effectiveStartDate: str
    meterId: str
    meterName: str
    productId: str
    skuId: str
    productName: str
    skuName: str
    serviceName: str
    serviceId: str
    serviceFamily: str
    unitOfMeasure: str
    type: str
    isPrimaryMeterRegion: bool
    armSkuName: str
    effectiveEndDate: str = ''
    reservationTerm: str = ''


@dataclass
class Response():
    BillingCurrency: str
    CustomerEntityId: str
    CustomerEntityType: str
    Items: Any
    NextPageLink: str
    Count: int


def download_file():
    logging.info('Downloading Azure Pricing API...')
    current_link = ''
    page = 1

    while current_link is not None:
        print(page)
        if current_link == '':
            current_link = basePricingURL

        response = requests.get(current_link)

        with open(f"data/azureretail-page-{page}.json", "wb") as handle:
            handle.write(response.content)

        next_page = response.json()['NextPageLink']
        current_link = next_page
        page += 1

        if page % 100 == 0:
            logging.info(f'Downloaded {page} pages Azure Pricing API')


def load_file():
    logging.info('Loading Azure pricing...')
    for filename in os.listdir('data'):
        if filename.startswith('azureretail-page-'):
            logging.info(f'Loading {filename}...')
            try:
                process_file('data/' + filename)
            except Exception as e:
                logging.error(f'Skipping {filename} due to {e}')


def process_file(fileName):
    logging.info(f'Processing {fileName}...')

    file = open(fileName,)
    data = json.load(file)
    response = Response(**data)
    products = map(lambda x: mapped_product(ProductRaw(**x)), response.Items)
    file.close()
    insert_product(products)


def mapped_product(product_raw: ProductRaw):
    product = Product(
        productHash='',
        sku=product_raw.skuId,
        vendorName='azure',
        region=product_raw.armRegionName,
        service=product_raw.serviceName,
        productFamily=product_raw.serviceFamily,
        attributes={
            'effectiveStartDate': product_raw.effectiveStartDate,
            'productId': product_raw.productId,
            'productName': product_raw.productName,
            'serviceId': product_raw.serviceId,
            'serviceFamily': product_raw.serviceFamily,
            'skuName': product_raw.skuName,
            'armSkuName': product_raw.armSkuName,
            'meterId': product_raw.meterId,
            'meterName': product_raw.meterName,
        },
        prices=[]
    )
    product.productHash = generate_product_hash(product)
    product.prices = mapped_price(product, product_raw)

    return product


def mapped_price(product: Product, product_raw: ProductRaw):
    prices = []

    instance_type = product_raw.type
    if product_raw.skuName.endswith('Spot'):
        instance_type = 'Spot'
    elif product_raw.skuName.endswith('Low Priority'):
        instance_type = 'Low Priority'

    price = Price(
        priceHash='',
        purchaseOption=instance_type,
        unit=product_raw.unitOfMeasure,
        price=product_raw.unitPrice,
        effectiveDateStart=product_raw.effectiveStartDate,
        startUsageAmount=product_raw.tierMinimumUnits
    )

    if product_raw.reservationTerm:
        price.termLength = product_raw.reservationTerm

    price.priceHash = generate_price_hash(product, price)
    prices.append(price)
    return prices
