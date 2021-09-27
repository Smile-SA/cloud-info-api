import sqlalchemy as sa
import json
from typing import List

from api.db.types import Product
from api.db.setup import db

def insert_product(products: List[Product]):
    insert_clause =  sa.text("""
        INSERT INTO pricing (productHash, sku, vendorName, region, service, productFamily, attributes, prices) VALUES
        (:productHash, :sku, :vendorName, :region, :service, :productFamily, :attributes, :prices)
        ON CONFLICT (productHash) DO UPDATE SET
        sku = excluded.sku,
        vendorName = excluded.vendorName,
        region = excluded.region,
        service = excluded.service,
        productFamily = excluded.productFamily,
        attributes = excluded.attributes,
        prices = pricing.prices || excluded.prices  
    """)

    table_name = 'pricing'
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