FROM python:2.7.12
RUN pip install pip==9.0.1
COPY requirements.txt /ansible/requirements.txt
RUN pip install -r requirements.txt
COPY ansible-playbooks /ansible/ansible-playbooks
COPY run.sh /ansible/run.sh
WORKDIR /ansible
ENTRYPOINT ["bash", "./run.sh"]
