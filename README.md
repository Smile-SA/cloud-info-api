# Cloud Pricing API

The API provides public prices for the virtual machine service available from AWS, Azure and GCP. The database of prices is automatically updated monthly via a scheduled job.

## Endpoints
### Download latest prices
**GET `/download`**

Download latest VMs prices from all providers. The prices will be stored in json file and ready to be digested and dumped into the database

### Load latest prices
**GET `/load`**

Parse pricing files, map relevant informations and write it to the database

### Query information
**POST `/query`**

Get the pricing information

Parameters expected:
- filter
- purchase_option

The parameter `purchase_option` can accept either these option:
- OnDemand
- Reserved
- Spot


Example for parameter `filter` for querying price for EC2 instance from AWS
```
{ "vendorName" : "aws", "productFamily": "Compute Instance" , "attributeFilters": [{"key": "instanceType", "value": "r5d.16xlarge"}, {"key": "tenancy", "value": "Shared"}, {"key": "operatingSystem", "value": "Linux"}]}
```

Example for the response
```
[
    {
        "memory": "512 GiB",
        "price": 0.012
        "vcpu": "64"
    },
]
```