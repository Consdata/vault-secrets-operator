import logging
import sys
from kubernetes import client, config, watch
import hvac
import base64

log = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.INFO)
log.addHandler(out_hdlr)
log.setLevel(logging.INFO)


def get_model(event):
    try:
        return dict(namespace=event['object']['metadata']['namespace'], res_name=event['object']['metadata']['name'],
                    name=event['object']['spec']['name'], path=event['object']['spec']['path'],
                    vault=event['object']['spec']['vault'], role=event['object']['spec']['role'],
                    type=event['object']['spec']['type'])
    except:
        return None


def get_body(data):
    out = {}
    for k, v in data.items():
        out[k] = base64.b64encode(bytes(v, 'utf-8')).decode("utf-8")
    return out


def update_secret(model):
    vault = hvac.Client(
        url=model["vault"])
    f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
    jwt = f.read()
    vault.auth_kubernetes(model["role"], jwt)
    response = vault.secrets.kv.read_secret_version(path=model['path'])

    body = dict(kind="Secret", apiVersion="v1", metadata=dict(name=model['name'], namespace=model['namespace']),
                data=get_body(response['data']['data']), type=model['type'])

    try:
        client.CoreV1Api().read_namespaced_secret(namespace=model['namespace'], name=model['name'])
        result = client.CoreV1Api().patch_namespaced_secret(name=model['name'], namespace=model['namespace'], body=body)
    except:
        result = client.CoreV1Api().create_namespaced_secret(namespace=model["namespace"], body=body)
    log.debug("{}".format(result))


def remove_secret(model):
    vault = hvac.Client(
        url=model["vault"])
    f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
    jwt = f.read()
    vault.auth_kubernetes(model["role"], jwt)
    response = vault.secrets.kv.read_secret_version(path=model["path"])

    try:
        client.CoreV1Api().read_namespaced_secret(namespace=model["namespace"], name=model["name"])
        client.CoreV1Api().delete_namespaced_secret(namespace=model["namespace"], name=model["name"])
        log.info(f"{model['namespace']}/{model['name']} removed")
    except kubernetes.client.exceptions.ApiException:
        log.error(f"{model['namespace']}/{model['name']} not found")

def main():
    log.info("Loading kube config")
    config.load_incluster_config()

    log.info("Waiting for events...")
    w = watch.Watch()
    for event in w.stream(client.CustomObjectsApi().list_cluster_custom_object, group="consdata.com", version="v1",
                          plural="vaultsecrets"):
        type = event['type']
        log.debug(event)
        if type == "ADDED" or type == "MODIFIED":
            model = get_model(event)
            log.info(
                f"[{type}] Secret detected namespace: {model['namespace']} name: {model['name']} path: {model['path']} vault: {model['vault']}")
            update_secret(model)

        elif type == "DELETED":
            model = get_model(event)
            log.info(
                f"[{type}] Secret detected namespace: {model['namespace']} name: {model['name']} path: {model['path']} vault: {model['vault']}")
            remove_secret(model)

        else:
            log.warn(f"Unsupported event type: {type}")


if __name__ == '__main__':
    main()