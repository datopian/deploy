#!/usr/bin/env bash

if [ "${1}" == "script" ]; then
    docker pull "${DOCKER_IMAGE}:latest"
    docker build --cache-from "${DOCKER_IMAGE}:latest" -t "${DOCKER_IMAGE}:latest" .
    [ "$?" != "0" ] && echo failed script && exit 1

elif [ "${1}" == "deploy" ]; then
    tag="${TRAVIS_COMMIT}"
    [ "${tag}" == "" ] && echo empty tag && exit 1
    docker login -u "${DOCKER_USER:-$DOCKER_USERNAME}" -p "${DOCKER_PASS:-$DOCKER_PASSWORD}" &&\
    docker push "${DOCKER_IMAGE}:latest" &&\
    docker tag "${DOCKER_IMAGE}:latest" "${DOCKER_IMAGE}:${tag}" &&\
    docker push "${DOCKER_IMAGE}:${tag}"
    [ "$?" != "0" ] && echo failed docker push && exit 1
    docker run -e CLONE_PARAMS="--branch ${K8S_OPS_REPO_BRANCH} https://github.com/${K8S_OPS_REPO_SLUG}.git" \
               -e YAML_UPDATE_JSON='{"'"${DEPLOY_VALUES_CHART_NAME}"'":{"'"${DEPLOY_VALUES_IMAGE_PROP}"'":"'"${DOCKER_IMAGE}:${tag}"'"}}' \
               -e YAML_UPDATE_FILE="${DEPLOY_YAML_UPDATE_FILE}" \
               -e GIT_USER_EMAIL="${DEPLOY_GIT_EMAIL}" \
               -e GIT_USER_NAME="${DEPLOY_GIT_USER}" \
               -e GIT_COMMIT_MESSAGE="${DEPLOY_COMMIT_MESSAGE}" \
               -e PUSH_PARAMS="https://${GITHUB_TOKEN}@github.com/${K8S_OPS_REPO_SLUG}.git ${K8S_OPS_REPO_BRANCH}" \
               orihoch/github_yaml_updater
    [ "$?" != "0" ] && echo failed github yaml update && exit 1

elif [ "${1}" == "trigger" ]; then
    body='{
      "request": {
      "message": "rebuild because '${TRAVIS_REPO_SLUG}'updated with commit '${TRAVIS_COMMIT}'",
      "branch":"master"
    }}'
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -H "Travis-API-Version: 3" \
      -H "Authorization: token ${TRAVIS_TOKEN}" \
      -d "$body" \
      https://api.travis-ci.com/repo/datahq%2F${TRIGGER_REPO}/requests
elif [ "${1}" == "pr" ]; then
    body='{
      "title": "'${DEPLOY_COMMIT_MESSAGE}'",
      "body": "'${GIT_PR_BODDY_MESSAGE}'",
      "head": "'${GIT_HEAD}'",
      "base": "'${GIT_PRODUCTION_BRANCH}'"
    }'
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -H "Authorization: token ${GITHUB_TOKEN}" \
      -d "$body" \
      https://api.github.com/repos/${TRAVIS_REPO_SLUG}/pulls
fi

echo Great Success
exit 0
