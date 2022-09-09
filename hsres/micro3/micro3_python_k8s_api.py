
from kubernetes import client, config
import kubernetes.client
import ssl
from kubernetes.client.rest import ApiException
from pprint import pprint

config = client.Configuration()

config.api_key['authorization'] = open('/var/run/secrets/kubernetes.io/serviceaccount/token').read()
config.api_key_prefix['authorization'] = 'Bearer'
config.host = 'https://kubernetes.default'
config.ssl_ca_cert = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
config.verify_ssl=True

list_client = client.CoreV1Api(client.ApiClient(config))

ret = list_client.list_namespaced_pod("default", watch=False)

print("Listing pods with their IPs:")

for i in ret.items:
    print(f"{i.status.pod_ip}\t{i.metadata.name}")

with kubernetes.client.ApiClient(config) as api_client:
    # Create an instance of the API class
    api_instance = kubernetes.client.AppsV1Api(api_client)
    name = 'hs-post-deploy' # str | name of the deployment

namespace='default'

api_response = api_instance.patch_namespaced_deployment_scale(
   name, namespace,
   [{'op': 'replace', 'path': '/spec/replicas', 'value': 1}])

#api_response = api_instance.patch_namespaced_deployment_scale(name, namespace, body, pretty=pretty, dry_run=dry_run, field_manager=fi>
#pprint(api_response)
