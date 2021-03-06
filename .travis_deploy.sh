#!/usr/bin/env bash

echo "${TRAVIS_COMMIT_MESSAGE}" | grep -- --no-deploy && echo skipping deployment && exit 0

K8S_ENVIRONMENT_NAME=${1}

openssl aes-256-cbc -K $encrypted_key -iv $encrypted_iv -in environments/"$K8S_ENVIRONMENT_NAME"/deploy-ops-secret.json.enc -out environments/"$K8S_ENVIRONMENT_NAME"/secret-k8s-ops.json -d

OPS_REPO_SLUG="datahq/deploy"
OPS_REPO_BRANCH="${TRAVIS_BRANCH}"
./run_docker_ops.sh "${K8S_ENVIRONMENT_NAME}" "
    RES=0;
    curl https://raw.githubusercontent.com/kubernetes/helm/v2.16.10/scripts/get > get_helm.sh && chmod 700 get_helm.sh && ./get_helm.sh;
    if ./helm_upgrade_all.sh --install --dry-run --debug; then
        echo Dry run was successfull, performing upgrades
        ! ./helm_upgrade_all.sh --install && echo Failed upgrade && RES=1
        ! ./helm_healthcheck.sh && echo Failed healthcheck && RES=1
    else
        echo Failed dry run
        RES=1
    fi
    sleep 2;
    kubectl get pods --all-namespaces;
    kubectl get service --all-namespaces;
    exit "'$'"RES
" "datopian/sk8s-ops" "${OPS_REPO_SLUG}" "${OPS_REPO_BRANCH}" "environments/"$K8S_ENVIRONMENT_NAME"/secret-k8s-ops.json"
if [ "$?" == "0" ]; then
    echo travis deployment success
    exit 0
else
    echo travis deployment failed
    exit 1
fi
