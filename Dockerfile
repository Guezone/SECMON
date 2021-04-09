FROM debian:latest
MAINTAINER Aubin Custodio (Guezone)
RUN apt update && apt install -y vim apache2 nano python3 git python3-pip libapache2-mod-wsgi-py3 net-tools dnsutils openssh-server openssl
RUN service apache2 stop
RUN rm /etc/apache2/sites-enabled/* && rm /etc/apache2/sites-available/*
RUN mkdir /etc/ssl/secmon/ && mkdir /var/www/secmon/
COPY ./ /var/www/secmon/
RUN cd /var/www/secmon/ && pip3 install -r requirements.txt && rm -Rf /var/www/html && cd /var/www/secmon/docker
EXPOSE 80
EXPOSE 443
EXPOSE 22 