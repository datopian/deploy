#!/usr/bin/env bash

echo "${TRAVIS_COMMIT_MESSAGE}" | grep -- --no-deploy && echo skipping deployment && exit 0

openssl aes-256-cbc -K $encrypted_075bf2c88471_key -iv $encrypted_075bf2c88471_iv -in environments/datahub-testing/deploy-ops-secret.json.enc -out environments/datahub-testing/k8s-ops-secret.json -d
K8S_ENVIRONMENT_NAME="datahub-testing"
OPS_REPO_SLUG="datahq/deploy"
OPS_REPO_BRANCH="${TRAVIS_BRANCH}"
./run_docker_ops.sh "${K8S_ENVIRONMENT_NAME}" "
    RES=0;
    curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get --version v2.8.2 > get_helm.sh && chmod 700 get_helm.sh && ./get_helm.sh;
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
" "orihoch/sk8s-ops" "${OPS_REPO_SLUG}" "${OPS_REPO_BRANCH}" "environments/datahub-testing/secret-k8s-ops.json"
if [ "$?" == "0" ]; then
    echo travis deployment success
    exit 0
else
    echo travis deployment failed
    exit 1
fi
