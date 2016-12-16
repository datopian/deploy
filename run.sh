#!/usr/bin/env bash
HELP=''
DEBUG=False
function print_help(){
  echo "usage: deploy.py [-h] [-d] {build,destroy}"
  echo ""
  echo "argument parser for ansible"
  echo ""
  echo "mandetory arguments:"
  echo "  -a, --action     {build, destroy}  please mention action"
  echo "optional arguments:"
  echo "  -h, --help       show this help message and exit"
  echo "  -d, --debug      Run in debug mode"
}

for i in "$@"
do
case $i in
    -a|--action)
    ACTION="$2"
    shift # past argument=value
    ;;
    -h|--help)
    HELP="TRUE"
    shift # past argument with no value
    ;;
    -d|--debug)
    DEBUG=True
    shift # past argument with no value
    ;;
    *)
    ;;
esac
shift
done

if [[ -z $ACTION ]]; then
  echo "Error in action name please see the help doc"
  print_help
  exit 0
fi
if [[ $HELP == "TRUE" ]]; then
  print_help
  exit 0
fi

if [[ $ACTION -eq 'build' ]];then
  ansible-playbook ansible-playbooks/deploy.yml --extra-vars "app_debug=${DEBUG}"
elif [[ $ACTION -eq 'destroy' ]]; then
  ansible-playbook ansible-playbooks/destroy.yml --extra-vars "app_debug=${DEBUG}"
fi
