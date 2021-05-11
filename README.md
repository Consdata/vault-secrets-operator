# Vault secrets operator

This operator allows creating k8s secrets with data from Vault KV secrets. To create new secret you need to apply custom resource:

```yaml
apiVersion: consdata.com/v1
kind: VaultSecret
metadata:
  name: test
spec:
  path: "k8s/test"
  vault: "http://0.0.0.0:8200"
  role: "k8s-operator"
  name: test-secret
  type: "kubernetes.io/dockerconfigjson"
```


| parameter | description
| --- | --- |
| path | Path to kv secret |
| vault | Vault host |
| role | K8s authentication role |
| name | K8s secret name |
| type | K8s secret type |

## Installation
```shell script

kubectl apply -f https://raw.githubusercontent.com/Consdata/vault-secrets-operator/master/operator.yml

```
