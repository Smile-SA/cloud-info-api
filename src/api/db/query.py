from dataclasses import dataclass
import sqlalchemy as sa
import json

from api.db.types import Price, Product
from api.db.setup import db
from typing import List, Dict


@dataclass
class ProductWithPrice():
    productHash: str
    sku: str
    vendorName: str
    region: str
    service: str
    productFamily: str
    attributes: Dict
    prices: List[Price]


def insert_product(products: List[Product]):
    insert_clause = sa.text("""
        INSERT INTO pricing ("productHash", "sku", "vendorName", "region", "service",
        "productFamily", "attributes", "prices") VALUES
        (:productHash, :sku, :vendorName, :region, :service,
        :productFamily, :attributes, :prices)
        ON CONFLICT ("productHash") DO UPDATE SET
        "sku" = excluded.sku,
        "vendorName" = excluded."vendorName",
        "region" = excluded.region,
        "service" = excluded.service,
        "productFamily" = excluded."productFamily",
        "attributes" = excluded.attributes,
        "prices" = pricing.prices || excluded.prices
    """)

    # table_name = 'pricing'
    for product in products:

        pricesMap = {}

        for price in product.prices:
            if price.priceHash in pricesMap.keys():
                pricesMap[price.priceHash].append(price.__dict__)
            else:
                pricesMap[price.priceHash] = [price.__dict__]

        # print(json.dumps(product.attributes))

        params = {
            # 'table_name': table_name,
            'productHash': product.productHash,
            'sku': product.sku,
            'vendorName': product.vendorName,
            'region': product.region,
            'service': product.service,
            'productFamily': product.productFamily,
            'attributes': json.dumps(product.attributes),
            'prices': json.dumps(pricesMap),
        }

        db.engine.execute(insert_clause.params(**params))


def find_product(other_filters, attributes_filters):
    table = 'pricing'
    tableClause = f'SELECT * FROM {table} WHERE '
    where_list = []

    for key in other_filters:
        where_list.append(filter_condition(key, other_filters[key]))

    for filter in attributes_filters:
        where_list.append(attribute_condition(filter))

    cond_clause = ' AND '.join(where_list)
    query = tableClause + cond_clause
    responses = db.engine.execute(query)
    products = []
    for response in responses:
        products.append(ProductWithPrice(**dict(response)))
    return products


def filter_condition(key, value):
    if isinstance(value, list):
        return f""""{key}" IN ({value})"""

    if value == '':
        return f"""("{key}" = '' OR {key} IS NULL)"""

    # Contains substring case
    if '%' in value:
        return f""""{key}" LIKE '{value}'"""

    return f""""{key}" = '{value}'"""


def attribute_condition(filter):
    if filter["value"] == '':
        return f"(attributes -> {filter['key']} IS NULL OR attributes ->>\
            {filter['key']} = '')"

    # Contains substring case
    if '%' in filter["value"]:
        return f"attributes ->> '{filter['key']}' LIKE '{filter['value']}'"

    return f"attributes ->> '{filter['key']}' = '{filter['value']}'"
