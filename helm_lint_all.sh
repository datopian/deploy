#!/usr/bin/env bash

RES=0

echo "Linting all charts"
for CHART_NAME in `ls charts-external`; do
    helm lint charts-external/$CHART_NAME 2>/dev/null | grep 'ERROR' | grep -v 'Chart.yaml: version is required'
    if [ "$?" == "0" ]; then
        echo "${CHART_NAME}: failed lint"
        RES=1
    else
        echo "${CHART_NAME}: OK"
    fi
done

exit $RES
