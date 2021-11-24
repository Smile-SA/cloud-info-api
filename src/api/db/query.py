import json
from dataclasses import dataclass
from typing import Any, Dict, List

from api.db.setup import db
from api.db.types import Price, Product

import sqlalchemy as sa


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
    """
    Add or update a product to the database.

    :products (List[Product]) Array of products

    """
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

    for product in products:

        prices_map = {}

        for price in product.prices:
            if price.priceHash in prices_map.keys():
                prices_map[price.priceHash].append(price.__dict__)
            else:
                prices_map[price.priceHash] = [price.__dict__]

        params = {
            'productHash': product.productHash,
            'sku': product.sku,
            'vendorName': product.vendorName,
            'region': product.region,
            'service': product.service,
            'productFamily': product.productFamily,
            'attributes': json.dumps(product.attributes),
            'prices': json.dumps(prices_map),
        }

        db.engine.execute(insert_clause.params(**params))


def find_product(other_filters: List, attributes_filters: List) -> List:
    """
    Find corresponding products by filters using a SQL query.

    :other_filters (List) Array of a filter of any field
    :attributes_filters (List) Array of a filter of the attributes field

    Return an array of matching products

    """
    table = 'pricing'
    table_clause = f'SELECT * FROM {table} WHERE '
    where_list = []

    for key in other_filters:
        where_list.append(filter_condition(key, other_filters[key]))

    for filter in attributes_filters:
        where_list.append(attribute_condition(filter))

    cond_clause = ' AND '.join(where_list)
    query = table_clause + cond_clause
    responses = db.engine.execute(query)
    products = []
    for response in responses:
        products.append(ProductWithPrice(**dict(response)))
    return products


def filter_condition(key: str, value: Any) -> str:
    """
    Convert filters into a SQL syntax.

    :key (str) Name of the condition
    :value (Any) Value of the condition, can be either a single value or a list

    Return a SQL string
    """
    if isinstance(value, list):
        return f""""{key}" IN ({value})"""

    if value == '':
        return f"""("{key}" = '' OR {key} IS NULL)"""

    # Contains substring case
    if '%' in value:
        return f""""{key}" LIKE '{value}'"""

    return f""""{key}" = '{value}'"""


def attribute_condition(filter: Any) -> str:
    """
    Convert filters into a SQL syntax.

    :filter (str) Array of filters

    Return a SQL string
    """
    if filter['value'] == '':
        return f"(attributes -> {filter['key']} IS NULL OR attributes ->>\
            {filter['key']} = '')"

    # Contains substring case
    if '%' in filter['value']:
        return f"attributes ->> '{filter['key']}' LIKE '{filter['value']}'"

    return f"attributes ->> '{filter['key']}' = '{filter['value']}'"
