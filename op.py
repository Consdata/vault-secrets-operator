import base64
import logging
import hvac
import kopf
from kubernetes import client


def get_body(data):
    out = {}
    for k, v in data.items():
        out[k] = base64.b64encode(bytes(v, 'utf-8')).decode("utf-8")
    return out


def secret_exists(namespace, secret):
    result = client.CoreV1Api().list_namespaced_secret(namespace=namespace)
    for i in result.items:
        if i.metadata.name == secret:
            return True
    return False


def upsert_secret(spec, namespace):
    vault = hvac.Client(url = spec["vault"])
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as f:
        jwt = f.read()
        vault.auth_kubernetes(spec["role"], jwt)
        response = vault.secrets.kv.read_secret_version(path=spec['path'])

        body = dict(kind="Secret", apiVersion="v1", metadata=dict(name=spec['name'], namespace=namespace),
        data = get_body(response['data']['data']), type = spec['type'])

        if secret_exists(namespace, spec['name']):
            result = client.CoreV1Api().patch_namespaced_secret(name=spec['name'], namespace=namespace, body=body)
            logging.debug("{}".format(result))
        else:
            logging.warning("{} secret not found. Creating.".format(spec['name']))
            result = client.CoreV1Api().create_namespaced_secret(namespace=namespace, body=body)
            logging.debug("{}".format(result))


def remove_secret(spec, namespace):
    if secret_exists(namespace, spec['name']):
        client.CoreV1Api().delete_namespaced_secret(namespace=namespace, name=spec["name"])
        logging.warning("{} secret removed".format(spec['name']))
    else:
        logging.warning("{} secret not found".format(spec['name']))


@kopf.on.update('consdata.com', 'v1', 'vaultsecrets')
@kopf.on.create('consdata.com', 'v1', 'vaultsecrets')
def update_handler(spec, **kwargs):
    upsert_secret(spec, kwargs['body']['metadata']['namespace'])


@kopf.on.delete('consdata.com', 'v1', 'vaultsecrets')
def delete_handler(spec, **kwargs):
    remove_secret(spec, kwargs['body']['metadata']['namespace'])
