docker buildx rm multiarch
docker buildx create --use --name multiarch
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64 -t consdata/vault-secrets-operator:0.1.0 -t consdata/vault-secrets-operator:latest --push .