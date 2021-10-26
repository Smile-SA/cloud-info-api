import googleapiclient.discovery

from flask import current_app
from oauth2client.client import GoogleCredentials
from api.db.types import Product, Price
from api.db.query import find_product, insert_product
from api.tools.hashing import generate_product_hash, generate_price_hash

credentials = GoogleCredentials.get_application_default()


machine_type_lookup = {
    'c2': {
        'cpu': 'Compute optimized Core%%',
        'memory': 'Compute optimized Ram%%',
    },
    'e2': {
        'cpu': 'E2 Instance Core%%',
        'memory': 'E2 Instance Ram%%',
    },
    'f1': {
        'total': 'Micro Instance with burstable CPU%%',
    },
    'g1': {
        'total': 'Small Instance with 1 VCPU%%',
    },
    'm1': {
        'cpu': 'Memory-optimized Instance Core%%',
        'memory': 'Memory-optimized%% Ram%%',
    },
    'n1': {
        'cpu': 'N1 Predefined Instance Core%%',
        'memory': 'N1 Predefined Instance Ram%%',
    },
    'n2': {
        'cpu': 'N2 Instance Core%%',
        'memory': 'N2 Instance Ram%%',
    },
    'n2d': {
        'cpu': 'N2D AMD Instance Core%%',
        'memory': 'N2D AMD Instance Ram%%',
    },
    'a2': {
        'cpu': 'A2 Instance Core%%',
        'memory': 'A2 Instance Ram%%',
    },
}


machine_type_override = {
    'e2-micro': {'cpu': 0.25},
    'e2-small': {'cpu': 0.5},
    'e2-medium': {'cpu': 1}
}


def load_machine():
    service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
    project_id = 'semafor-321815'

    region_req = service.regions().list(project=project_id)
    products = []

    def filter_zone(region, zone):
        zone_index = zone.find(region)
        return zone[zone_index:len(zone)]

    while region_req is not None:
        region_resp = region_req.execute()
        for region in region_resp['items']:
            region_name = region['name']
            region_zones = list(map(lambda x: filter_zone(region_name, x),
                                region['zones']))
            if region_zones[0] == 'europe-west3-c':
                machine_types_req = service.machineTypes().list(project=project_id,
                                                                zone=region_zones[0])
                while machine_types_req is not None:
                    machine_types_resp = machine_types_req.execute()

                    for machine_type in machine_types_resp['items']:
                        machine_name = machine_type['name']
                        current_app.logger.info(f'Adding machine type {machine_name} \
                            for region {region_name}...')

                        product = Product(
                            productHash='',
                            sku=f'generated-{machine_name}',
                            vendorName='gcp',
                            region=region_name,
                            service='Compute Engine',
                            productFamily='Compute Instance',
                            attributes={
                                'machineTypes': machine_name,
                            },
                            prices=[]
                        )

                        product.productHash = generate_product_hash(product)
                        on_demand_price = create_price(product, machine_type, 'on_demand')
                        preemptible_price = create_price(product, machine_type, 'preemptible')
                        if on_demand_price:
                            product.prices.append(on_demand_price)
                        if preemptible_price:
                            product.prices.append(preemptible_price)
                        products.append(product)

                    machine_types_req = service.machineTypes().list_next(previous_request=machine_types_req, previous_response=machine_types_resp)
        region_req = service.regions().list_next(previous_request=region_req, previous_response=region_resp)
    insert_product(products)


def create_price(product, machine_type, purchase_option):
    machine_name = machine_type['name']
    machine_family = machine_name.split('-')[0]

    if machine_family not in machine_type_lookup:
        current_app.logger.warn('Description does not exist for machine type {machine_name}')
        return None

    if 'total' in machine_type_lookup[machine_family]:
        result = generate_price_total(product, machine_type, purchase_option)
    else:
        result = generate_price_cpu_memory(product, machine_type, purchase_option)
        product.attributes['vcpu'] = result['vcpu']
        product.attributes['memory'] = result['mem']

    if not result:
        return None

    price = Price(
        priceHash='',
        purchaseOption=purchase_option,
        unit='Hours',
        price=result['price'],
        effectiveDateStart=result['effectiveDateStart']
    )
    price.priceHash = generate_price_hash(product, price)
    return price


def generate_price_total(product, machine_type, purchase_option):
    machine_type_name = machine_type['name']
    machine_family = machine_type_name.split('-')[0]

    description = machine_type_lookup[machine_family]['total']

    if purchase_option == 'preemptible':
        description = f'Spot Preemptible {description}'

    matched_vm = find_compute(product.region, description)

    if not matched_vm:
        current_app.logger.warn(f'No matching found for VM type {machine_type_name} \
            by purchase {purchase_option}')
        return None

    matched_price = matched_vm.prices[list(matched_vm.prices)[0]][0]
    price = matched_price['price']
    effective_datestart = matched_price['effectiveDateStart']
    return {'price': price, 'effectiveDateStart': effective_datestart}


def generate_price_cpu_memory(product, machine_type, purchase_option):
    machine_type_name = machine_type['name']
    machine_family = machine_type_name.split('-')[0]

    cpu_desc = machine_type_lookup[machine_family]['cpu']
    mem_desc = machine_type_lookup[machine_family]['memory']

    if purchase_option == 'preemptible':
        cpu_desc = f'Spot Preemptible {cpu_desc}'
        mem_desc = f'Spot Preemptible {mem_desc}'

    matched_cpu_vm = find_compute(product.region, cpu_desc)
    matched_mem_vm = find_compute(product.region, mem_desc)

    if not matched_cpu_vm:
        current_app.logger.warn(f'No matching found for VM CPU type {matched_cpu_vm} \
         by purchase {purchase_option}')
        return None

    if not matched_mem_vm:
        current_app.logger.warn(f'No matching found for VM Memory type {matched_mem_vm} \
            by purchase {purchase_option}')
        return None

    cpu = float(machine_type['guestCpus'])
    mem = float(machine_type['memoryMb']) / 1024

    if machine_type_name in machine_type_override:
        cpu = machine_type_override[machine_type_name]['cpu']

    matched_cpu_price = matched_cpu_vm.prices[list(matched_cpu_vm.prices)[0]][0]
    matched_mem_price = matched_mem_vm.prices[list(matched_mem_vm.prices)[0]][0]

    price = cpu * float(matched_cpu_price['price']) + \
        mem * float(matched_mem_price['price'])
    effective_datestart = matched_cpu_price['effectiveDateStart']
    return {
        'price': price,
        'effectiveDateStart': effective_datestart,
        'vcpu': str(cpu),
        'mem': str(mem),
    }


def find_compute(region, description):
    filter = {
        'vendorName': 'gcp',
        'service': 'Compute Engine',
        'productFamily': 'Compute',
        'region': region,
    }
    attribute_filter = [{
        'key': 'description',
        'value': description
    }]
    products = find_product(filter, attribute_filter)

    result = products[0] if len(products) > 0 else None
    return result
