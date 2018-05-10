#!/usr/bin/env bash

# this script can run using source - to enable keeping the environment variables and shell completion
#
# please pay attention not to call exit in this script - as it might exit from the user's shell
#
# thanks for your understanding and cooperation

k8s_connect_gke() {
	export CLOUDSDK_CORE_PROJECT
	export CLOUDSDK_CONTAINER_CLUSTER
	export CLOUDSDK_COMPUTE_ZONE
	export K8S_NAMESPACE
	export K8S_HELM_RELEASE_NAME
	export K8S_ENVIRONMENT_NAME
	export K8S_ENVIRONMENT_CONTEXT
  kubectl config set-context "${K8S_ENVIRONMENT_CONTEXT}" "--namespace=${K8S_NAMESPACE}" >/dev/null
  kubectl config use-context "${K8S_ENVIRONMENT_CONTEXT}"
  [ "${K8S_CONNECT_ORIGINAL_PS1}" == "" ] && export K8S_CONNECT_ORIGINAL_PS1="${PS1}"
  export PS1="${K8S_CONNECT_ORIGINAL_PS1}\[\033[01;33m\]${CLOUDSDK_CORE_PROJECT}-${CLOUDSDK_CONTAINER_CLUSTER}-${K8S_NAMESPACE}\[\033[0m\]$ "
  source <(kubectl completion bash)
  echo "Connected to ${CLOUDSDK_CORE_PROJECT}-${CLOUDSDK_CONTAINER_CLUSTER}-${K8S_NAMESPACE}"
}

k8s_connect_custom() {
	export K8S_NAMESPACE
	export K8S_HELM_RELEASE_NAME
	export K8S_ENVIRONMENT_NAME
	export K8S_ENVIRONMENT_CONTEXT
  kubectl config set-context "${K8S_ENVIRONMENT_CONTEXT}" "--namespace=${K8S_NAMESPACE}" >/dev/null
  kubectl config use-context "${K8S_ENVIRONMENT_CONTEXT}"
  [ "${K8S_CONNECT_ORIGINAL_PS1}" == "" ] && export K8S_CONNECT_ORIGINAL_PS1="${PS1}"
  export PS1="${K8S_CONNECT_ORIGINAL_PS1}\[\033[01;33m\]`kubectl config current-context 2>/dev/null`\[\033[0m\]$ "
  source <(kubectl completion bash)
  echo "Connected to ${K8S_ENVIRONMENT_CONTEXT}"
}

if [ -f .env ] && eval `dotenv -f ".env" list` \
   && [ "${CLOUDSDK_CORE_PROJECT}" != "" ] \
   && [ "${CLOUDSDK_CONTAINER_CLUSTER}" != "" ] \
   && [ "${CLOUDSDK_COMPUTE_ZONE}" != "" ] \
   && [ "${K8S_NAMESPACE}" != "" ] \
   && [ "${K8S_HELM_RELEASE_NAME}" != "" ] \
   && [ "${K8S_ENVIRONMENT_NAME}" != "" ] \
   && [ "${K8S_ENVIRONMENT_CONTEXT}" != "" ] \
   && [ "${K8S_ENVIRONMENT_CONTEXT}" == "`kubectl config current-context 2>/dev/null`" ]; then
	k8s_connect_gke
elif [ "${CLOUDSDK_CORE_PROJECT}" == "" ] && [ "${CLOUDSDK_CONTAINER_CLUSTER}" == "" ] && [ "${CLOUDSDK_COMPUTE_ZONE}" == "" ]
then
    k8s_connect_custom
elif ! gcloud "--project=${CLOUDSDK_CORE_PROJECT}" \
            container clusters get-credentials "$CLOUDSDK_CONTAINER_CLUSTER" \
            "--zone=${CLOUDSDK_COMPUTE_ZONE}" >/dev/null 2>&1; then
    echo
    echo "Failed to connect! Please ensure you have permissions and are logged in to gcloud. You can connect manually to debug:"
    echo
    echo "gcloud container clusters get-credentials $CLOUDSDK_CONTAINER_CLUSTER --zone "${CLOUDSDK_COMPUTE_ZONE}""
    echo
else
  K8S_ENVIRONMENT_CONTEXT=`kubectl config current-context`
  dotenv -qnever set "K8S_ENVIRONMENT_CONTEXT" "${K8S_ENVIRONMENT_CONTEXT}"
  k8s_connect_gke
fi
