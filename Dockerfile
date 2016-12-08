FROM python:2.7.12
RUN pip install pip==9.0.1
RUN pip install ansible==2.2.0.0
RUN pip install PyJWT==1.4.2
RUN pip install boto==2.43.0
COPY ansible-playbooks /ansible/ansible-playbooks
COPY run.sh /ansible/run.sh
WORKDIR /ansible
ENTRYPOINT ["bash", "./run.sh"]
