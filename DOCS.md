# Table of contents
- [Table of contents](#table-of-contents)
- [Installation](#installation)
  - [With docker](#with-docker)
    - [Autosetup](#autosetup)
    - [Automation](#automation)
  - [Without docker](#without-docker)
    - [Setup](#setup)
    - [Automation](#automation-1)
    - [Startup](#startup)
    - [Configuration of the web service](#configuration-of-the-web-service)
- [Login](#login)
- [Configuration](#configuration)
  - [Search products](#search-products)
  - [Add your products](#add-your-products)
  - [User interface](#user-interface)
    - [CVE Module](#cve-module)
    - [RSS Module](#rss-module)
    - [Settings](#settings)
- [Upgrade](#upgrade)
- [Logging](#logging)
  - [Useful logs](#useful-logs)
  - [Error logs](#error-logs)

# Installation


Before installation, you must have drawn up :

- The list of products present in your infrastructure by their common name without version (ex: ```Apache;Microsoft Windows;CentOS```)
- The list of CPE product identifiers present on your infrastructure (ex: ```cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:x64:*;cpe:2.3:o:apple:mac_os:-:*:*:*:*:*```)

**Note 1** : You can also upload a CSV file with one line per product via the web interface but I advise you to put the list at the installation.

**Note 2** : Product names (keywords) should not be too succinct (e.g. prefer to use 'Microsoft Office' instead of 'Office'). This could avoid false positives during alerts.

You will be able to search and add new products after installation via the web UI.

## With docker

With the docker installation, everything is automated. The script creates a self-signed certificate if you wish and configures apache. Obviously, you can change the configuration according to your needs.

The installation with Docker allows via a volume (-v option) to easily update SECMON with Git.

To update it, you will have to : 
- Go to the folder where SECMON was cloned at installation
- Add the current folder as a local repo
- Do a git pull to get the changes

The files will then be modified directly in your SECMON container.


### Autosetup
```bash
sudo git clone https://github.com/Guezone/SECMON && cd SECMON
sudo docker build . -t secmon:latest
sudo docker network create --driver=bridge --subnet=10.10.10.0/24 --gateway=10.10.10.254 SECMON_NET
sudo docker run -i -t --hostname secmonsrv --ip 10.10.10.100 --name secmon-srv -v YOUR_CURRENT_PARENT_PATH/SECMON/:/var/www/secmon --network SECMON_NET --expose 80 --expose 443 -d secmon:latest
sudo docker exec -it secmon-srv python3 /var/www/secmon/docker/install.py
```
```
| SECMON - DockerAutoInstall |
1. Certificate : 
Note 1 : You can delete this self signed cert and put your CA signed cert after install. 
Enter the FQDN of the web server :secmon.demo.net
Note 2 : Don't forget to enter a good value for CN (FQDN of your server)
Generating a RSA private key
........................................................................++++
...................................................................................................................++++
writing new private key to '/etc/ssl/secmon/secmon.key'
-----
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [AU]:FR
State or Province Name (full name) [Some-State]:IDF
Locality Name (eg, city) []:Paris
Organization Name (eg, company) [Internet Widgits Pty Ltd]:SecmonDemo
Organizational Unit Name (eg, section) []:X
Common Name (e.g. server FQDN or YOUR name) []:secmon.demo.net
Email Address []:XXXXXXXXXXX@XXXX.XX
Your certificate is available on /etc/ssl/secmon ! 
----------------------------------------------------------------------------------------------------------------------
2. SECMON Install : 
Sender email address : sender@mail.com
Sender email account password :XXXXXXXXXXXXXXXXXXXX
SMTP Server FQDN or IP :XXXX.XXXX.XXXX
SMTP used port :587
Using TLS SMTP auth ? (yes/no) :yes
Language (en/fr) :fr
SECMON email receivers (single or many seperated by ;):receiver1@mail.com;receiver2@mail.com 

------------------------------------
SECMON setup script - Version 1.0.0
------------------------------------
SECMON is licensed by CC BY-NC-SA 4.0 license. Do you accept the terms of the license? (y/Y;n/N) : y

Let's go to add your products list for which you want to check the new CVEs. 
 Of course, you can add more with the web interface after installation !

Do you want to use keyword (for CVE polling) (y/Y;n/N) : y

Please enter the keywords you are interested in among CVE publications separated by ';' (ex: Forti;F5;BigIP;Cisco)  :VMWare;PAN-OS;Forti;F5;BigIP;Cisco;iOS;Microsoft Exchange;Microsoft Office;Wireshark
Do you want to use a list of CPEs (NVD product reference) to complete the keyword search? (y/Y;n/N) : y

Please enter the CPEs for which you want to report the CVE (ex: cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:x64:*;cpe:2.3:o:apple:mac_os:-:*:*:*:*:*:*:*) separated by ';'' :cpe:2.3:o:microsoft:windows_10:1909:*:*:*:*:*:*:*;cpe:2.3:a:apache:http_server:2.4.44:*:*:*:*:*:*:*

Do you want to use a Github API for exploit retrieval (y/Y;n/N) : y

Please enter your Github username : XXXXXXXXXXX
Please enter your Github API Token : XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Enter the username that can be used on the Web UI : demo_user
Enter the password (please choose a strong password !) : XXXXXXXX
Confirm the password : XXXXXXXX

RSS news database recording in progress...

Successful build database.

CVE database recording in progress...This operation can take a few minutes to a few hours. Take a coffee! :D

Successful build database.

Please wait. A test message to receiver1@mail.com will be sent to test your configuration.
Please wait. A test message to receiver2@mail.com will be sent to test your configuration.

SECMON is now ready. Execute secmon.py now and automate it.
Executing secmon in background...
Executing cve_updater in background...
SECMON is successfully installed and configured !
----------------------------------------------------------------------------------------------------------------------
3. Apache configuration : 
Considering dependency setenvif for ssl:
Module setenvif already enabled
Considering dependency mime for ssl:
Module mime already enabled
Considering dependency socache_shmcb for ssl:
Enabling module socache_shmcb.
Enabling module ssl.
See /usr/share/doc/apache2/README.Debian.gz on how to configure SSL and create self-signed certificates.
To activate the new configuration, you need to run:
  service apache2 restart
[ ok ] Restarting Apache httpd web server: apache2.
Apache is successfully configured !
You can now access the web interface at the following address: https://secmon.demo.net
----------------------------------------------------------------------------------------------------------------------

```

### Automation

Edit the **host crontab** with **vi /etc/crontab** command, for example like this :

```bash
0 * * * * root docker exec secmon-srv python3 /var/www/secmon/secmon.py >> /var/log/secmon 2>&1
0 6 * * * root docker exec secmon-srv python3 /var/www/secmon/cve_updater.py >> /var/log/secmon-updates 2>&1
@reboot root docker start secmon-srv
@reboot root docker exec secmon-srv service apache2 start
@reboot root docker exec secmon-srv service ssh start

```

This configuration automates the retrieval of new CVE (and news) every 20 minutes and an update of the scores and associated products every day at 6am.

Now, you can login to SECMON with a giving URL. 

## Without docker

### Setup


```bash
sudo apt update
sudo apt install -y python3 python3-pip apache2 libapache2-mod-wsgi-py3 git
sudo git clone https://github.com/Guezone/SECMON
cd SECMON
sudo pip3 install -r requirements.txt
sudo rm -Rf /var/www/html
sudo mkdir /var/www/secmon && sudo cp -r * /var/www/secmon/ && cd /var/www/secmon/
sudo python3 setup.py -sender sender@mail.com -p 'XXXXXXXXXXXXXXXX' -login [your SMTP login, often email address] -server srv.mail.com -port 587 -tls yes -lang fr -r 'receiver1@mail.com;receiver2@mail.com'
```
**Note :** The installation script may take a few minutes or even a few hours. You can also add your product list after install and press "n" on the two instructions.

**Output :** 

```bash
------------------------------------
SECMON setup script - Version 1.0.0
------------------------------------
SECMON is licensed by CC BY-NC-SA 4.0 license. Do you accept the terms of the license? (y/Y;n/N) : y

Let's go to add your products list for which you want to check the new CVEs. 
 Of course, you can add more with the web interface after installation !

Do you want to use keyword (for CVE polling) (y/Y;n/N) : y

Please enter the keywords you are interested in among CVE publications separated by ';' (ex: Forti;F5;BigIP;Cisco)  :VMWare;PAN-OS;Forti;F5;BigIP;Cisco;iOS;Microsoft Exchange;Microsoft Office;Wireshark
Do you want to use a list of CPEs (NVD product reference) to complete the keyword search? (y/Y;n/N) : y

Please enter the CPEs for which you want to report the CVE (ex: cpe:2.3:o:microsoft:windows_server_2008:r2:sp1:*:*:*:*:x64:*;cpe:2.3:o:apple:mac_os:-:*:*:*:*:*:*:*) separated by ';'' :cpe:2.3:o:microsoft:windows_10:1909:*:*:*:*:*:*:*;cpe:2.3:a:apache:http_server:2.4.44:*:*:*:*:*:*:*

Do you want to use a Github API for exploit retrieval (y/Y;n/N) : y

Please enter your Github username : XXXXXXXXXXX
Please enter your Github API Token : XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Enter the username that can be used on the Web UI : demo_user
Enter the password (please choose a strong password !) : XXXXXXXX
Confirm the password : XXXXXXXX

RSS news database recording in progress...

Successful build database.

CVE database recording in progress...This operation can take a few minutes to a few hours. Take a coffee! :D

Successful build database.

Please wait. A test message to receiver1@mail.com will be sent to test your configuration.
Please wait. A test message to receiver2@mail.com will be sent to test your configuration.

SECMON is now ready. Execute secmon.py now and automate it.
```
### Automation

Edit your crontab with **sudo vi /etc/crontab** command, for example like this :

```bash

0 * * * * root python3 /var/www/secmon/secmon.py >> /var/log/secmon 2>&1
0 6 * * * root python3 /var/www/secmon/cve_updater.py >> /var/log/secmon-updates 2>&1

```

This configuration automates the retrieval of new CVE (and news) every 20 minutes and an update of the scores and associated products every day at 6am.

### Startup
Launch the main script of the application : 

```bash
sudo python3 secmon.py 
Cloning exploit-database repository                        <-- At the first launch only, there is a download of the exploit-db.com exploit database.
Clonage dans 'exploit-database'...
remote: Enumerating objects: 194, done.
remote: Counting objects: 100% (194/194), done.
remote: Compressing objects: 100% (163/163), done.
remote: Total 135299 (delta 72), reused 139 (delta 31), pack-reused 135105
Réception d'objets: 100% (135299/135299), 151.14 MiB | 3.94 MiB/s, fait.
Résolution des deltas: 100% (85326/85326), fait.
Extraction des fichiers: 100% (44380/44380), fait.
------------ CVE Module ------------                      
Starting at : 30/11/2020 23:09:30
------------------------------------
Configuration is good.
------------------------------------
Polling NVD RSS feed (keyword based search).

No new CVE matched with your keyword list.
------------------------------------
Polling NVD related to your product list (CPE based search).

No new CVE related to your (CPE) product list
------------------------------------
Finished at : 30/11/2020 23:09:38
------------------------------------

------------ RSS Module ------------
Starting at : 30/11/2020 23:09:38
------------------------------------
Configuration is good.
------------------------------------
No news. Goodbye.
------------------------------------
Finished at : 30/11/2020 23:09:44
------------------------------------
```

At this step, SECMON is properly configured and you can receive alerts about new CVE that affect your products as well as new "cyber" news.

You now need to update the list of available exploits for each CVE (exploit-db and Github) as well as your high security risk products.

**Note :** "high security risk" products are those that have :

- Critical and high vulnerabilities (based on the CVSS 3.0 score)
- Vulnerabilities where there are known exploits (Github or Exploit-DB)

To make this update : 

```bash
sudo python3 cve_updater.py 
------------ CVE Module - Update ------------
Starting at : 30/11/2020 23:34:06
---------------------------------------------
Refreshing exploit-database repo with latest exploits
From https://github.com/offensive-security/exploit-database
 * branch                master     -> FETCH_HEAD
Already up to date.
Refreshing EDBID-CVE mapping
100% (43828 of 43828) |###############################################################################################| Elapsed Time: 0:00:00 Time:  0:00:00
Exploit found for CVE-2021-3156 from Exploit-DB
Exploit found for CVE-2014-8380 from Exploit-DB

Search Github Exploit for registered CVE...
Exploit found for CVE-2020-1590 from Github

Updating high risk product list....
New critical product : Microsoft Windows Server 2008 R2

Updating affected products and CVSS score related to your CVE list...
No CVE have been updated.

---------------------------------------------
Finished at : 30/11/2020 23:52:24
---------------------------------------------
```
**Note :** This operation can take a few minutes to a few hours.

### Configuration of the web service

You must then delete the Apache sites configured by default : 

```bash
sudo rm /etc/apache2/sites-enabled/*
sudo rm /etc/apache2/sites-available/*
sudo a2enmod wsgi
sudo a2enmod ssl
```
Then, you have to create a new configuration file dedicated to SECMON (in ```/etc/apache2/sites-available/secmon.conf```) : 

Here is an example of configuration for a "secure" basic configuration : 

```bash
ServerName secmon.corp.net
<VirtualHost *:80>
      ServerAdmin admin@mail.com
      ServerName secmon.corp.net
      ServerAlias www.secmon.corp.net
      DocumentRoot /var/www/secmon
      Redirect permanent / https://secmon.corp.net
      <Directory /var/www/secmon>
          WSGIProcessGroup secmon_web
          WSGIPassAuthorization On
          WSGIApplicationGroup %{GLOBAL}
          Order deny,allow
          Allow from all
      </Directory>
      ServerSignature off
      ErrorLog ${APACHE_LOG_DIR}/error_secmon.log
      CustomLog ${APACHE_LOG_DIR}/access_secmon.log combined
</VirtualHost>
<VirtualHost *:443>
      WSGIScriptAlias / /var/www/secmon/secmon.wsgi
      WSGIDaemonProcess secmon_web
      DocumentRoot /var/www/secmon
      ServerName  secmon.corp.net
      ServerAlias www.secmon.corp.net
      <Directory /var/www/secmon>
          WSGIProcessGroup secmon_web
          WSGIPassAuthorization On
          WSGIApplicationGroup %{GLOBAL}
          Order deny,allow
          Allow from all
      </Directory>
      ServerSignature Off
      LogLevel info
      ErrorLog ${APACHE_LOG_DIR}/error_secmon.log
      CustomLog ${APACHE_LOG_DIR}/access_secmon.log combined
      SSLProtocol -all +TLSv1.2 +TLSv1.3
      SSLEngine on
      SSLCertificateFile PATH/YOUR_CERT.crt
      SSLCertificateKeyFile PATH/YOUR_PRIVATE_KEY.key
</VirtualHost>
```
**Note :** You can use a self-signed certificate or a certificate signed by a known CA. This configuration must be changed according to your settings and is an example.

```bash
sudo a2ensite secmon
Enabling site secmon.
To activate the new configuration, you need to run:
  systemctl reload apache2


sudo systemctl reload apache2

cd /var/www/secmon && sudo chown -R www-data:www-data .
sudo chmod -R 744 .
```

# Login

Now you will be able to connect to the Web UI with the credentials entered during installation : 

![](https://github.com/Guezone/SECMON/blob/master/img/login.png)

SECMON is now fully ready to use ! It's time for a ☕.

# Configuration

## Search products

SECMON accepts the "products" to be supervised in keywords or in CPE (Common Platform Enumeration).

The keywords are used when the CVE do not have a CPE filled in and this is particularly the case when it has just been published.

In SECMON's WEB UI, go to the **Settings -> Product management** tab. You have at your disposal a search section in order to find the CPE references by their common name (example for Windows Server 2019) :

![](https://github.com/Guezone/SECMON/blob/master/img/product-search.png)


CPEs allow greater accuracy down to the product version level. CPEs can only be found when they have been provided by the publisher, which is not always the case. You can still use previous versions to determine this.

Example :
```
The CPE search for Apache 2.4.46 does not find the correct CPE code but the CPE code for version 2.4.44 is "cpe: 2.3: a: apache: http_server: 2.4.44: *: *: *: *: *: *: * "

All you have to do is replace the correct fields with the correct version: "cpe: 2.3: a: apache: http_server: 2.4.46: *: *: *: *: *: *: *"
```

## Add your products

To add new products to your list, go to the **Settings -> Product management** tab then to the ** Manage product ** section. You then have the choice to add / delete a CPE or a keyword :

![](https://github.com/Guezone/SECMON/blob/master/img/product-add.png)

You can also import a list of products (CPE and keywords) into a CSV in the same tab. It must consist of a single command. Example file :

```csv
cpe:2.3:a:keepass:password_safe:*:*:*:*:*:*:*:*
cpe:2.3:o:microsoft:windows_10:2004:*:*:*:*:*:*:*
cpe:2.3:a:docker:docker:0.2.1:*:*:*:*:*:*:*
cpe:2.3:a:anydesk:anydesk:*:*:*:*:*:*:*:*
cpe:2.3:o:vmware:esxi:7.0:*:*:*:*:*:*:*
Microsoft Exchange
Microsoft Office
HPE
F5
BigIP
Extreme
```

**Note**: when you add a CPE reference, it may take several minutes or even several hours for all the CVEs to be recorded in the database. To follow the progress, go to the tab **Settings -> Tasks**. A good practice might be to set the keywords to match your CPE references ("Docker" as a keyword and "cpe:2.3:a:docker:docker:0.2.1:*:*:*:*:*:*"as a CPE).

## User interface

**Home**: dashboard allowing you to see the state of health of your fleet regarding vulnerabilities. Products with high security risks appear as well as the rate of corrected / read / unread vulnerabilities.

### CVE Module

**Search**: this page allows you to search for details about a CVE

**Vulnerability management**: this page allows you to put a stamp in order to know the status of the correction of your vulnerability. For better management, I encourage you to indicate when you became aware of a vulnerability and also when it is fixed. Once the alert has been sent by email, I also encourage you to check that the CVE concerns your product with the exact version. There may be false positives in particular on the search for CVE by keyword, you can also note the false on this page.

**Last CVE alerts**: this page allows you to view vulnerabilities by product and also to see the list of high risk products, ie those with exploitable vulnerabilities.

**Exploits**: allows you to search for exploits linked to a CVE and also to see the list of exploitable CVEs. The source of the information is based on Github and Exploit-DB.

**Last CVE updates**: Allows you to see if recent changes have been made to CVSS scores or affected products regarding your vulnerabilities.

### RSS Module

**Cybersecurity news**: this page allows you to view the latest information and articles identified by the tool.

### Settings

**Logs**: allows you to view the logs produced by the tool.

**Product management**: this page allows you to search for CPE references, add / remove products (keywords or CPE) to your list and display the list.

**SMTP Configuration**: allows you to change the SMTP configuration linked to sending CVE alerts or news.

**Tasks**: allows you to view the status of recent tasks which are heavy for SECMON. Today, only the addition of products appears here as it is a process that can be very long.

You can update your web UI password and also add users. To do this, click on the menu at the top right and then go to **Account settings**.

**Note** : It is currently impossible to reset passwords via a token and email as is usually the case.

# Upgrade

The installation of SECMON with Docker allows the use of a volume in order to have a "synchronisation" between the host and the container.

If you want to have the latest version of SECMON with the latest changes, go to the folder where SECMON was cloned (on the host) and run the following commands:

```
git pull origin
sudo chown -R www-data:www-data .
sudo chmod -R 744 .
sudo docker exec -it secmon-srv service apache2 restart
```

The files will be updated on the host side and in the container and SECMON will be updated.

If you are not using docker, you can do the same in the folder where the repository was cloned. However, you will need to copy the modified files to **/var/www/secmon** and also assign the correct rights. You will also have to restart the Apache service.

# Logging

## Useful logs

All useful SECMON logs are written to your **/var/www/secmon/logs.txt**. The format is not really standard but they are parsed automatically by Splunk for example. 

Obviously, I encourage you to create alerts if you have a SIEM to manage critical vulnerabilities and high-risk products in your regular processes.

Here is an example of field extractions (Graylog compatible file): 

**Note**: you can obviously reuse the **Grok patterns** contained in the file to extract fields on your log collection and analysis tools.

```json
{
  "extractors": [
    {
      "title": "SECMON-Authentication-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "cut",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=%{GREEDYDATA:script} server=\"%{IP:dst_ip}\" src_ip=\"%{IPV4:src_ip}\" username=\"%{USERNAME:username}\" auth_status=\"%{WORD:status}\" message=\"%{GREEDYDATA:msg}\""
      },
      "condition_type": "regex",
      "condition_value": "auth_status"
    },
    {
      "title": "SECMON-CVE-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "cut",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=\"%{GREEDYDATA:script}\" server=\"%{IP:dst_ip}\" cve_id=\"%{GREEDYDATA:cve_id}\" type=\"%{WORD:type}\" matched_product=\"%{GREEDYDATA:matched_product}\" cvss_score=\"%{GREEDYDATA:cvss_score}\" severity=\"%{GREEDYDATA:severity}\" cve_date=\"%{GREEDYDATA:cve_date}\" cpes=\"%{GREEDYDATA:cpes}\" report=\"%{WORD:report}\" alert=\"%{WORD:alert}\" message=\"%{GREEDYDATA:msg}\""
      },
      "condition_type": "string",
      "condition_value": "cve_id"
    },
    {
      "title": "SECMON-Exploits-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "cut",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=%{GREEDYDATA:script} server=\"%{IP:dst_ip}\" cve=\"%{GREEDYDATA:cve_id}\" exploit_source=\"%{GREEDYDATA:exploit_source}\" message=\"%{GREEDYDATA:msg}\""
      },
      "condition_type": "string",
      "condition_value": "exploit"
    },
    {
      "title": "SECMON-Tasks-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "copy",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=%{GREEDYDATA:script} server=\"%{IP:dst_ip}\" task_id=\"%{INT:task_id}\" task_status=\"%{WORD:task_status}\" message=\"%{GREEDYDATA:msg}\""
      },
      "condition_type": "string",
      "condition_value": "task_id"
    },
    {
      "title": "SECMON-News-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "cut",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=%{GREEDYDATA:script} server=\"%{IP:dst_ip}\" feed=\"%{GREEDYDATA:feed}\" feed_url=\"%{URI:feed_url}\" news_title=\"%{GREEDYDATA:news_title}\" news_url=\"%{URI:news_url}\" mail=\"%{WORD:mail}\""
      },
      "condition_type": "string",
      "condition_value": "rss_poller"
    },
    {
      "title": "SECMON-HighRiskProducts-Extract",
      "extractor_type": "grok",
      "converters": [],
      "order": 0,
      "cursor_strategy": "cut",
      "source_field": "message",
      "target_field": "",
      "extractor_config": {
        "grok_pattern": "%{TIMESTAMP_ISO8601:timestamp} source_script=%{GREEDYDATA:script} server=\"%{IP:dst_ip}\" cpe=\"%{GREEDYDATA:cpe}\" hname=\"%{GREEDYDATA:hname}\" message=\"%{GREEDYDATA:msg}\""
      },
      "condition_type": "string",
      "condition_value": "A new critical product"
    }
  ],
  "version": "4.0.5"
}
```

## Error logs

The error logs generated by the pollers will be located where you redirect the standard output in your cron configuration.

Error logs related to your web interface will be available in the Apache error file (or other depending on your usage). The errors are normally formatted.

Feel free to file an issue on Github if you see an error.
