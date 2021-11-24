import unittest

from api.db.types import Price, Product
from api.tools.hashing import generate_price_hash, generate_product_hash


class TestHashing(unittest.TestCase):

    def test_product_hashing(self):
        """Test that the hashing process for product works properly."""
        product_input = Product(
            vendorName='aws',
            sku='P2ABFKWDYEZQ7ZT7'
        )
        expected_result = '980485f89b08e6e0dcf3328cb4574126'
        result = generate_product_hash(product=product_input)
        self.assertEqual(result, expected_result)

    def test_price_hasing(self):
        """Test that the hashing process for product price works properly."""
        product_input = Product(
            vendorName='aws',
            sku='F3674HBWVZZUS39J'
        )
        result_product_hash = generate_product_hash(product=product_input)
        expected_product_result = 'b25b6d5b7438a3ecc2623741e8d85e3d'
        self.assertEqual(result_product_hash, expected_product_result)

        product_input.productHash = expected_product_result

        price_input = Price(
            purchaseOption='reserved',
            unit='Hrs',
            termLength='',
            termPurchaseOption='',
            termOfferingClass=''
        )
        expected_price_result = 'b25b6d5b7438a3ecc2623741e8d85e3d-'\
            '8e1b9d285b137c4121eb8aecd5a75e23'
        result_price_hash = generate_price_hash(product=product_input, price=price_input)
        self.assertEqual(result_price_hash, expected_price_result)
