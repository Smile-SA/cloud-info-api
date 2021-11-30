# Cloud Info API
<a href="https://hub.docker.com/r/alterwayrnd/cloud-info-api/tags"><img alt="Docker Image" src="https://img.shields.io/badge/docker-passing-brightgreen"/></a>
<a href="https://github.com/alterway/cloud-info-api/actions"><img alt="Build Status" src="https://img.shields.io/github/workflow/status/alterway/cloud-info-api/Upload Docker image/main"/></a>

The API provides public prices for the virtual machine service available from AWS, Azure and GCP. The database of prices is automatically updated monthly via a scheduled job.

## Deployment
The API supports a deployment using Helm Chart to deploy into a Kubernetes cluster.

Installing the chart will automatically create 2 pods:
- Cloud Info API
- PostgresSQL

**Prerequisites**
- Kubernetes Cluster 1.12+
- Helm
- PV provisioner support in the underlying infrastructure

**Dependencies**
- postgresql (10.12.7)

**Instruction**

Run the command below

```
helm install cloud-pricing  ./cloud-pricing
```

It will deploy into your current namespaces two pods, it should look like this
```
NAME                             READY   STATUS    RESTARTS   AGE
cloud-pricing-6b5cf4db97-bh4t5   1/1     Running   0          5d6h
cloud-pricing-postgresql-0       1/1     Running   0          5d6h
```

Once the API has been deployed and marked Running, you can access the API via port `localhost:5042`


## Endpoints
### Download latest prices
**GET `/download`**

Download latest VMs prices from all providers. The prices will be stored in json file and ready to be digested and dumped into the database

### Load latest prices
**GET `/load`**

Parse pricing files, map relevant information and write it to the database

### Query information
**POST `/query`**

Get the pricing information

Parameters expected:
- filter
- purchase_option

The parameter `purchase_option` can accept either these options:
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
        "memory": 512,
        "price": 0.012,
        "cpu": 64
    },
]
```

## Contributing
We are glad to receive issues and pull requests from you, please kindy read our [contributing](CONTRIBUTING.md) guide for more information. 

## Credits
This project is heavily inspired by the project [Cloud Pricing API](https://github.com/infracost/cloud-pricing-api) developed by the folks @`infracost`. Big thanks to them.