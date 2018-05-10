#!/usr/bin/env bash

# this script can run using source - to enable keeping the environment variables and shell completion
#
# please pay attention not to call exit in this script - as it might exit from the user's shell
#
# thanks for your understanding and cooperation

! which kubectl >/dev/null && echo "attempting automatic installation of kubectl" && gcloud --quiet components install kubectl
! which helm >/dev/null && echo "attempting automatic installation of helm" && curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh && chmod 700 get_helm.sh && ./get_helm.sh
! which dotenv >/dev/null && echo "attempting automatic installation of python-dotenv" && sudo pip install python-dotenv
! which jq >/dev/null && echo "attempting automatic installation of jq" && sudo apt-get update && sudo apt-get install -y jq

if which dotenv >/dev/null && which helm >/dev/null && which kubectl >/dev/null && which jq >/dev/null; then
  if [ "${1}" == "" ]; then
      echo "source switch_environment.sh <ENVIRONMENT_NAME>"
  else
  	ENVIRONMENT_NAME="${1}"	
  	if [ ! -f "environments/${ENVIRONMENT_NAME}/.env" ]; then
  		echo "missing environments/${ENVIRONMENT_NAME}/.env"
  	else
  		[ -f .env ] && eval `dotenv -f ".env" list`
  		echo "Switching to ${ENVIRONMENT_NAME} environment"
  		rm -f .env
  		if ! ln -s "`pwd`/environments/${ENVIRONMENT_NAME}/.env" ".env"; then
  			echo "Failed to symlink .env file"
  		else
  			source connect.sh
  		fi
  	fi
  fi
else
  echo "Failed to install dependencies, please try to install manually"
fi
