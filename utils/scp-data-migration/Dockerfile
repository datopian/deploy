FROM alpine:3.7
RUN apk update && apk add openssh-client bash
COPY entrypoint.sh /
ENTRYPOINT ["bash", "/entrypoint.sh"]
