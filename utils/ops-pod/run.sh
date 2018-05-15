#!/usr/bin/env bash

NAME="${1}"
[ -z "${NAME}" ] && echo a unique name argument is required && exit 1

EXTRA_VALUES="${2}"
! [ -z "${EXTRA_VALUES}" ] && EXTRA_VALUES=",${EXTRA_VALUES}"

EXEC_PARAMS="${@:3}"
[ -z "${EXEC_PARAMS}" ] && EXEC_PARAMS="sh"

helm delete --purge "${NAME}" >/dev/null 2>&1 && while kubectl get pods "${NAME}"; do sleep 1; printf .; done
helm upgrade "${NAME}" utils/ops-pod --install --set "name=${NAME}${EXTRA_VALUES}" &&\
while [ "$(kubectl get pods "${NAME}" '-ojsonpath={.status.phase}')" != "Running" ]; do
    sleep 1
    printf .
done &&\
kubectl exec -it "${NAME}" $EXEC_PARAMS
RES=$?
kubectl delete pod "${NAME}"
exit $RES
