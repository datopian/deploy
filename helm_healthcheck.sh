#!/usr/bin/env bash

source connect.sh

RES=0

echo "Performing health checks for all charts of ${K8S_ENVIRONMENT_NAME} environment"

for CHART_NAME in `ls charts-external`; do
    if ! [ "`./read_env_yaml.sh ${CHART_NAME} enabled`" == "true" ]; then
        echo ${CHART_NAME}: disabled, skipping healthcheck
    elif ! bash charts-external/${CHART_NAME}/healthcheck.sh; then
        echo ${CHART_NAME}: ERROR
        RES=1
    else
        echo ${CHART_NAME}: OK
    fi
done

[ "${RES}" == "0" ] && echo Great Success!

exit $RES
