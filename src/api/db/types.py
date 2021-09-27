from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Price():
    priceHash: str
    purchaseOption: str
    unit: str
    price: str
    effectiveDateStart: str
    effectiveDateEnd: str = ''
    startUsageAmount: str = ''
    endUsageAmount: str = ''
    termLength: str = ''
    termPurchaseOption: str = ''
    termOfferingClass: str = ''
    description: str = ''

@dataclass
class Product():
    productHash: str
    sku: str
    vendorName: str
    region: str
    service: str
    productFamily: str
    attributes: Dict
    prices: List[Price]