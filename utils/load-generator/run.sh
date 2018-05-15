#!/usr/bin/env bash

NAME="${1}"
[ -z "${NAME}" ] && echo a unique name argument is required && exit 1

EXTRA_VALUES="${2}"
! [ -z "${EXTRA_VALUES}" ] && EXTRA_VALUES=",${EXTRA_VALUES}"

helm delete --purge "${NAME}" >/dev/null 2>&1 && while kubectl get pods "${NAME}"; do sleep 1; printf .; done
helm upgrade "${NAME}" utils/load-generator --install --set "name=${NAME}${EXTRA_VALUES}" &&\
while true; do
    if kubectl logs -f "${NAME}"; then
        echo
        kubectl delete pod "${NAME}"
        exit 0
    else
        sleep 1
    fi
done
