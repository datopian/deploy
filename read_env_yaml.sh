#!/usr/bin/env bash

source connect.sh >/dev/null

ENV_AUTO_VALUE="`./read_yaml.py environments/${K8S_ENVIRONMENT_NAME}/values.auto-updated.yaml "$@" 2>/dev/null`"
if [ "${ENV_AUTO_VALUE}" != "" ] && [ "${ENV_AUTO_VALUE}" != "{}" ]; then
    echo "${ENV_AUTO_VALUE}"
    exit 0
fi

ENV_MAN_VALUE="`./read_yaml.py environments/${K8S_ENVIRONMENT_NAME}/values.yaml "$@" 2>/dev/null`"
if [ "${ENV_MAN_VALUE}" != "" ] && [ "${ENV_MAN_VALUE}" != "{}" ]; then
    echo "${ENV_MAN_VALUE}"
    exit 0
fi

ROOT_VALUE="`./read_yaml.py ./values.yaml "$@" 2>/dev/null`"
if [ "${ROOT_VALUE}" != "" ] && [ "${ROOT_VALUE}" != "{}" ]; then
    echo "${ROOT_VALUE}"
    exit 0
fi

exit 1
