#!/usr/bin/env bash

source connect.sh

# force an update for a K8S deployment by setting a label with unix timestamp

[ "${1}" == "" ] && echo "usage: ./force_update.sh <deployment_name|all>" && exit 1

ALL_DEPLOYMENT_NAMES="auth
                      list-manager
                      data-api
                      search-api
                      app-generic-item
                      app-main-page
                      app-search
                      socialmap-app-main-page
                      openprocure-app-main-page
                      nginx"

patch_deployment() {
    kubectl patch deployment "${1}" -p "{\"spec\":{\"template\":{\"metadata\":{\"labels\":{\"date\":\"`date +'%s'`\"}}}}}"
}

if [ "${1}" == "all" ]; then
    RES=0
    for deployment_name in $ALL_DEPLOYMENT_NAMES; do
        echo "${deployment_name}"
        ! patch_deployment "${deployment_name}" && RES=1
    done
    [ "${RES}" != "0" ] && exit "${RES}"
    for deployment_name in $ALL_DEPLOYMENT_NAMES; do
        echo "${deployment_name}"
        kubectl rollout status deployment "${deployment_name}"
    done
    exit "${RES}"
else
    patch_deployment "${1}" && kubectl rollout status deployment "${1}"
fi
