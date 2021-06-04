# SECMON - Infosec Watching Tool <center><img src="https://github.com/Guezone/SECMON/blob/master/img/logo.jpg" data-canonical-src="https://github.com/Guezone/SECMON/blob/master/img/logo.png" width="30" height="30" /></center> 

[![made-with-python, 🖤 and ☕](https://img.shields.io/badge/Made%20with-Python%2C%20%F0%9F%96%A4%20and%20%E2%98%95-blue)](https://www.python.org/)  ![Version](https://img.shields.io/badge/Version-2.0-blue)  ![Stage](https://img.shields.io/badge/Stage-Beta-yellow)  ![GitHub contributors](https://img.shields.io/github/contributors/Guezone/SECMON?label=Contributors)  ![Tested on](https://img.shields.io/badge/Tested%20on-Debian%2010%20&%20Docker-brightgreen)  ![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0%20(Non--commercial)-red)  ![Discord](https://img.shields.io/discord/826868157838262282?color=6A7EC2&label=Discord&logo=https%3A%2F%2Fimg.shields.io%2Fdiscord%2F783381738558455897.svg&logoColor=7389D8&style=plastic)  ![Website](https://img.shields.io/website?down_color=red&down_message=Offline&label=Demo&up_color=green&up_message=Online&url=https%3A%2F%2Fsecmon.guezone.info%2F)




![](https://github.com/Guezone/SECMON/blob/master/img/dashboard.png)

# Description

SECMON is a **web-based tool** for the automation of **infosec watching** and **vulnerability management** with a web interface.

A demo is available [here](https://secmon.guezone.info/). A Discord channel is available [here](https://discord.gg/cXzvb4fKzE)

## Features

- **Mail alerting** when a **new CVE** is published and which concerns your product list
- **Mail alerting** when a "cyber-security" news are published: new threats, recent attacks, events, etc.
- Visualize the **high security risk products** present on your IT infrastructure
- Download CVE **Excel report** by date range
- Display **top cybersecurity subject** (**Light cyber landscape**)
- Logs **easy to integrate in a SIEM** (verified on **Splunk** and **Graylog**)
- View the **latest CVE** and **latest news related to cyber security are published**
- Assign a buffer of **management status of a CVE**
- Search all the **details of a CVE** 
- Check if there is an **exploit** on **Github or Exploit-DB** concerning a CVE 
- Search for **vulnerabilities for a specified product**
- **Manage your product list**: search/add/delete a product, display your referenced product list
- **Monitor the sources** used by pollers 

Email alerts can be sent in English or French. SECMON web UI now support multi user account.

CVE are polled using two methods of collection/correspondence: 

- **Keyword-based** : allows you to be proactive on the retrieval of CVE by leaving a little bit of precision (no version check, just word matching) on the affected products (ex: "VMWare", "Apache").
- **CPE based** (Common Platform Enumeration) : allows the retrieval of CVE that only concern the product version entered (e.g. "Windows 10 1909", "Apache 2.4.38")

## Requirements
SECMON requires registration on Github API for exploits retrieval. It also requires : 

- OS : Linux-based system (tested on Debian 10)
- Environnement : Python 3 (tested on Python 3.9 and Python 3.8)

**WARNING** : Web UI credentials are hashed (SHA512 with salt), on the other hand, the Github API connection credentials and the application session key are neither encrypted nor hashed. All data is stored in an unencrypted sqlite database. A few advices :

- Allow access to this machine only to persons who are authorized to do so.
- Isolate the host machine from the rest.
- Use a dedicated server/VM or Docker container.

## Some screenshots

![](https://github.com/Guezone/SECMON/blob/master/img/mail_alert_sample.png) 

<p align="center"><i>Example of email alerts (CVE and RSS)</i></p> 

![](https://github.com/Guezone/SECMON/blob/master/img/vulnmgmt.png) 

<p align="center"><i>Vulnerability management page</i></p>

![](https://github.com/Guezone/SECMON/blob/master/img/cve_search.png)

<p align="center"><i>CVE details</i></p>

![](https://github.com/Guezone/SECMON/blob/master/img/exploits.png)

<p align="center"><i>Exploit search</i></p>

![](https://github.com/Guezone/SECMON/blob/master/img/cyber-threats.png)

<p align="center"><i>Cyber threats top subject</i></p>

![](https://github.com/Guezone/SECMON/blob/master/img/product-search.png)

<p align="center"><i>Product search</i></p>

![](https://github.com/Guezone/SECMON/blob/master/img/product-list.png)

<p align="center"><i>Product list</i></p>

# Installation

[Read the docs](DOCS.md)

# Thanks
Thanks to <a href="https://github.com/andreafioraldi" target='_blank'>@andreafioraldi</a> for <a href="https://github.com/andreafioraldi/cve_searchsploit" target='_blank'>cve_searchsploit</a> Python module.

Thanks to <a href="https://github.com/konsav" target='_blank'>@konsav</a> for <a href="https://github.com/konsav/email-templates" target='_blank'>HTML/CSS email template.</a>

Thanks to <a href="https://github.com/rodolfo-mendes" target='_blank'>@rodolfo-mendes</a> for <a href="https://github.com/rodolfo-mendes/sbadmin2-flask-template" target='_blank'>the sbadmin2 (Bootstrap) template adapted to Flask.</a>

Thanks to Florent Chatain for the first web security auditing.

# License
**SECMON** (by Aubin Custodio - Guezone) is licensed under **CC BY-NC-SA 4.0**.

This license allows you to **use** SECMON, to **improve it** and to make it live **by mentioning the author** but **without using it for commercial purposes**. As the infosec watching process is quite difficult and time consuming, it should only be used to help companies and/or users **to secure their IT infrastructure** and to know the current cyber security world.

# Changelog 

**2.0 :**


- Modification of the log format
- Reporting method (generation via dates)
- Web UI - new boostrap template 
- Work on the Docker automation part

**2.1 :**

- Add a multi-user support on Web UI
- Improved auto docker configuration (to improve updates with git and volume)
- Added a **Cyber Threats** section that highlights the top cyber topics reported in the RSS module
- Update of README and DOCS (docker, update & screenshots part)
- Prioritisation of the CPE polling method over the keyword method

# Roadmap

- [x] Automate the deployment with docker
- [x] First security auditing (front-end only)
- [ ] Create script to allow CPE scanning on Windows and Linux based system
- [ ] Add new sources of cyber-news
- [X] Write user documentation for the Web UI
- [ ] Create a REST API for calling in other applications
- [x] Write the logs in a standard format and plan to send them to a third party of SIEM type.
- [ ] Send CVE daily update report (new high risk product, CVSS changes, affected product changes, new exploitable CVE)
