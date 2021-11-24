from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Price():
    purchaseOption: str = ''
    unit: str = ''
    price: str = ''
    effectiveDateStart: str = ''
    priceHash: str = ''
    effectiveDateEnd: str = ''
    startUsageAmount: str = ''
    endUsageAmount: str = ''
    termLength: str = ''
    termPurchaseOption: str = ''
    termOfferingClass: str = ''
    description: str = ''


@dataclass
class Product():
    sku: str = ''
    vendorName: str = ''
    region: str = ''
    service: str = ''
    productFamily: str = ''
    productHash: str = ''
    attributes: Dict = field(default_factory=lambda: {})
    prices: List[Price] = field(default_factory=lambda: [])
