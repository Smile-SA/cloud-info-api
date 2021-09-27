import requests
import json

basePricingURL = 'https://cloudbilling.googleapis.com/v1'

class Sku(object):
    def __init__(self, name, skuId, description, category, serviceRegions, pricingInfo, serviceProviderName, geoTaxonomy) -> None:
        self.name = name
        self.skuId = skuId
        self.description = description
        self.category = category
        self.serviceRegions = serviceRegions
        self.pricingInfo = pricingInfo
        self.serviceProviderName = serviceProviderName
        self.geoTaxonomy = geoTaxonomy

def parse_product():
    apiKey = 'AIzaSyDN4Eqx_AEME8GplWZnqTU-MuysvJH_d3Y'
    sku = '6F81-5844-456A'
    pricingWithKeyURL = f'{basePricingURL}/services/{sku}/skus?key={apiKey}'
    response = requests.get(pricingWithKeyURL).json()
    
    # for sku in response["skus"]:
    skuPayload = response["skus"][0]
    # print(skuPayload)
    # skuPayload = json.loads(sku)
    skuParsed = Sku(**skuPayload)
    print(skuParsed.name)

