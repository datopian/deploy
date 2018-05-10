#!/usr/bin/env bash

source connect.sh

RES=0

echo "Upgrading all charts of ${K8S_ENVIRONMENT_NAME} environment"
for CHART_NAME in `ls charts-external`; do
    ./helm_upgrade_external_chart.sh "${CHART_NAME}" "$@"
    [ "$?" != "0" ] && echo "failed ${CHART_NAME} upgrade" && RES=1;
done

exit $RES
