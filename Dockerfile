FROM debian:latest
MAINTAINER Aubin Custodio (Guezone)
RUN apt update && apt install -y vim apache2 nano python3 git python3-pip libapache2-mod-wsgi-py3 net-tools dnsutils openssh-server openssl
RUN service apache2 stop
RUN rm /etc/apache2/sites-enabled/* && rm /etc/apache2/sites-available/*
RUN mkdir /etc/ssl/secmon/ && mkdir /var/www/secmon/
COPY ./requirements.txt /tmp
RUN cd /tmp && pip3 install -r requirements.txt && rm -Rf /var/www/html
EXPOSE 80
EXPOSE 443
EXPOSE 22 