#!/usr/bin/env bash

source connect.sh

CHART_NAME="${1}"

[ -z "${CHART_NAME}" ] && echo "usage:" && echo "./helm_upgrade_external_chart.sh <EXTERNAL_CHART_NAME>" && exit 1

RELEASE_NAME="${K8S_HELM_RELEASE_NAME}-${CHART_NAME}-${K8S_ENVIRONMENT_NAME}"
EXTERNAL_CHARTS_DIRECTORY="charts-external"
CHART_DIRECTORY="${EXTERNAL_CHARTS_DIRECTORY}/${CHART_NAME}"

echo "RELEASE_NAME=${RELEASE_NAME}"
echo "CHART_DIRECTORY=${CHART_DIRECTORY}"

[ ! -e "${CHART_DIRECTORY}" ] && echo "CHART_DIRECTORY does not exist" && exit 1

TEMPDIR=`mktemp -d`
echo '{}' > "${TEMPDIR}/values.yaml"

for VALUES_FILE in values.yaml values.auto-updated.yaml environments/${K8S_ENVIRONMENT_NAME}/values.yaml environments/${K8S_ENVIRONMENT_NAME}/values.auto-updated.yaml
do
    if [ -f "${VALUES_FILE}" ]; then
        GLOBAL_VALUES=`./read_yaml.py "${VALUES_FILE}" global 2>/dev/null`
        ! [ -z "${GLOBAL_VALUES}" ] \
            && ./update_yaml.py '{"global":'${GLOBAL_VALUES}'}' "${TEMPDIR}/values.yaml"
        RELEASE_VALUES=`./read_yaml.py "${VALUES_FILE}" "${CHART_NAME}" 2>/dev/null`
        ! [ -z "${RELEASE_VALUES}" ] \
            && ./update_yaml.py "${RELEASE_VALUES}" "${TEMPDIR}/values.yaml"
    fi
#    cat "${TEMPDIR}/values.yaml"
done

VALUES=`cat "${TEMPDIR}/values.yaml"`

if [ "`./read_yaml.py "${TEMPDIR}/values.yaml" enabled 2>/dev/null`" == "true" ]; then
    CMD="helm upgrade -i -f ${TEMPDIR}/values.yaml ${RELEASE_NAME} ${CHART_DIRECTORY} ${@:2}"
    if ! $CMD; then
        echo
        echo "${TEMPDIR}/values.yaml"
        echo "${VALUES}"
        echo
        echo "CMD"
        echo "${CMD}"
        echo
        echo "helm upgrade failed"
        exit 1
    else
        rm -rf $TEMPDIR
        echo "Great Success!"
        exit 0
    fi
else
    echo "chart is disabled, not performing upgrade"
    exit 0
fi
