import googleapiclient.discovery

from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()


def scrape():
    service = googleapiclient.discovery.build('compute', 'v1')
    projecy_id = 'semafor-321815'
    zone = 'europe-west3-b'
    machinetypesReq = service.machineTypes().list(project=projecy_id, zone=zone)

    while machinetypesReq is not None:
        response = machinetypesReq.execute()

        for machine_type in response['items']:
            print(machine_type)
