#!/usr/bin/env bash

( [ -z "${KEY_FILE}" ] || [ -z "${SSH_USER}" ] || [ -z "${SSH_HOST}" ] ||\
  [ -z "${FROM_PATH}" ] || [ -z "${TO_PATH}" ] ) &&\
        echo missing environment variables && exit 1

! [ -e "${KEY_FILE}" ] && echo missing KEY_FILE && exit 1

TEMPDIR=`mktemp -d` &&\
cp "${KEY_FILE}" "${TEMPDIR}/key" &&\
chmod 400 "${TEMPDIR}/key" &&\
scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
    -rvCi "${TEMPDIR}/key" \
    "${SSH_USER}@${SSH_HOST}:${FROM_PATH}" "${TO_PATH}"
