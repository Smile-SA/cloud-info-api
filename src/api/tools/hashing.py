import hashlib

from api.db.types import Price, Product


def generate_product_hash(product: Product) -> str:
    """
    Generate a hashed string based on product informations.

    :product (Product) Product object

    Return a hashed string
    """
    hash_field = ['vendorName', 'sku']

    hash_values = []
    for field in hash_field:
        hash_values.append(getattr(product, field))

    hash_str = hashlib.md5('-'.join(hash_values).encode())
    hash_str = hash_str.hexdigest()

    return hash_str


def generate_price_hash(product: Product, price: Price) -> str:
    """
    Generate a hashed string based on product price informations.

    :product (Product) Product object
    :price (Price) Product price object

    Return a hashed string
    """
    hash_field = [
        'purchaseOption',
        'unit',
        'termLength',
        'termPurchaseOption',
        'termOfferingClass'
    ]

    hash_values = []
    for field in hash_field:
        hash_values.append(getattr(price, field))

    hash_str = hashlib.md5('-'.join(hash_values).encode())
    hash_str = hash_str.hexdigest()

    return product.productHash + '-' + hash_str
