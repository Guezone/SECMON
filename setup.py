# -*- coding: utf-8 -*-
""" 
SECMON - Source code of the SECMON setup script.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
import sys, base64, time, os, smtplib,argparse, re, sqlite3, feedparser, requests
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from secmon_lib import pollCveIdFromCpe, registerNewCve, getCpeList, getKeywordsList
from datetime import datetime, timedelta
from getpass import getpass
rss_feeds = [ 
    'https://cyware.com/allnews/feed',
    'https://www.cshub.com/rss/categories/attacks',
    'https://www.schneier.com/feed/atom/',
    'https://www.cshub.com/rss/categories/cloud' ,
    'https://www.cshub.com/rss/categories/iot',
    'https://www.cshub.com/rss/categories/data',
    'https://www.cshub.com/rss/categories/executive-decisions',
    'https://www.cshub.com/rss/categories/network',
    'https://krebsonsecurity.com/feed/',
    'https://www.cshub.com/rss/categories/threat-defense',
    'https://www.fortiguard.com/rss/ir.xml',
    'https://nakedsecurity.sophos.com/feed/',
    'https://www.techrepublic.com/rssfeeds/topic/security/?feedType=rssfeeds',
    'http://feeds.feedburner.com/TheHackersNews?format=xml',
    'https://www.cert.ssi.gouv.fr/feed/',
    'https://us-cert.cisa.gov/ncas/all.xml',
    'https://www.zataz.com/feed/'
]

def mailTester(smtp_login, smtp_passwd, smtpsrv, port, tls, sender, receivers, language):
    print()
    configBuilder(smtp_login, smtp_passwd, smtpsrv, port, tls, sender, receivers, language)
    buildRSSList(rss_feeds)
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("setup.py","")
    body = ""
    receivers_email = receivers.split(";")
    with open(dir_path+'rss_template.html', 'r') as template:
        html_code = template.read()
    html_code = html_code.replace("Notification","SECMON")
    html_code = html_code.replace("<strong>Title : </strong> $TITLE <br><br>","")
    html_code = html_code.replace("<strong>Source : </strong> $SOURCE <br><br>","")
    if language =="en" or language == "EN":
        html_code = html_code.replace("RSS module","Test email")
        html_code = html_code.replace("<strong>Summary :</strong> $SUMMARY <br>","SECMON is an active security watch program that alerts you to the latest vulnerabilities and threats.")
        html_code = html_code.replace("Responsive HTML email templates","SECMON - Test email.")
        html_code = html_code.replace("See more details","Follow me on Github")
        body = html_code.replace("URL OF THE NEWS","https://github.com/Guezone/SECMON")

    elif language =="fr" or language == "FR":
        html_code = html_code.replace("RSS module","Mail de test")
        html_code = html_code.replace("<strong>Summary :</strong> $SUMMARY <br>","SECMON est un programme de veille sécurité active\net vous averti des dernières vulnérabilités et menaces.")
        html_code = html_code.replace("Responsive HTML email templates","SECMON - Mail de test.")
        html_code = html_code.replace("See more details","Suivez-moi sur Github")
        html_code = html_code.replace("This email was sent by", "Cet email a été envoyé par")
        body = html_code.replace("URL OF THE NEWS","https://github.com/Guezone/SECMON")   
    else:
        print("Incorrect language set. Please retry. Exiting...")     
    for receiver in receivers_email:
        try:
            print("\nPlease wait. A test message to {} will be sent to test your configuration.\n".format(receiver))
            smtpserver = smtplib.SMTP(smtpsrv,port)
            msg = MIMEMultipart()
            if language =="en" or language == "EN":
                msg['Subject'] = 'SECMON - Test email.'
            elif language =="fr" or language == "FR":
                msg['Subject'] = 'SECMON - Mail de test.'
            else:
                print("Incorrect language set. Please retry. Exiting...")  
                
            msg['From'] = sender
            msg['To'] = receiver
            msg.attach(MIMEText(body, 'html'))
        except:
            print("Incorrect configuration. Exit")
            exit()
        try:
            if tls == "yes":
                smtpserver.ehlo()
                smtpserver.starttls()
                smtpserver.login(smtp_login, smtp_passwd)
                smtpserver.sendmail(sender, receiver, msg.as_string())
            elif tls == "no":
                smtpserver.login(smtp_login, smtp_passwd)
                smtpserver.sendmail(sender, receiver, msg.as_string())
            else:
                print("You must specify if you want to use TLS(-tls yes|no). Exit.")
                exit()      
        except Exception as e:
            print(e)
            print("An error occurred during authentication with the SMTP server. Check the configuration and try again.")
            exit()
    print("SECMON is now ready. Execute secmon.py now and automate it.")
def buildRSSList(rss_feeds):
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("setup.py","")
    print("\nRSS news database recording in progress...\n")
    con = sqlite3.connect(dir_path+'secmon.db')
    con.execute('''CREATE TABLE RSS_DATA ([key] INTEGER PRIMARY KEY,[RSS_URL] text,[title] text,[rss_f] text,[summary] text)''')
    cur = con.cursor()
    con.commit()
    con.execute('''CREATE TABLE CVE_DATA ([key] INTEGER PRIMARY KEY,[CVE_ID] text,[KEYWORD] text,[STATUS] text,[CVE_SCORE] text,[CVE_DATE] text,[CVE_DESCRIPTION] text,[CVE_EVAL] text,[CVE_CPE] text,[CVE_SOURCES] text,[EXPLOIT_FIND] text,[INDEXING_DATE] text)''')
    con.execute('''CREATE TABLE high_risk_products ([key] INTEGER PRIMARY KEY,[cpe] text,[hname] text)''')
    con.execute('''CREATE TABLE tasks ([key] INTEGER PRIMARY KEY,[task_id] text,[status] text,[comment] text)''')
    con.commit()
    for rss_feed in rss_feeds:
        current_feed = feedparser.parse(rss_feed)
        for entries in current_feed.entries:
            url = str(entries.link)
            title = entries.title
            summary = entries.summary
            cur.execute("INSERT INTO RSS_DATA (RSS_URL, title, rss_f, summary) VALUES (?,?,?,?);", (url,title,rss_feed,summary))
            con.commit()
    print("Successful build database.\n")

def configBuilder(smtp_login, smtp_passwd, smtpsrv, port, tls, sender, receiver, language):
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("setup.py","")
    try:
        os.system(f"touch {dir_path}logs.txt")
        os.system(f"chmod 777 {dir_path}logs.txt")
    except:
        pass
    enc_pass = (str(base64.b64encode(smtp_passwd.encode("UTF-8"))).replace("b'","")).replace("'","")
    if os.path.isfile(dir_path+"secmon.db"):
        os.remove(dir_path+"secmon.db")
    con = sqlite3.connect(dir_path+'secmon.db')
    con.execute('''CREATE TABLE config ([key] INTEGER PRIMARY KEY,[sender] text,[smtp_login] text,[smtp_password] text,[smtpsrv] text,[port] text,[receiver] text,[tls] text,[language] text,[github_api_key] text,[github_username] text,[cvss_alert_limit] text,[no_score_cve_alert] text)''')
    con.execute('''CREATE TABLE keyword_list ([key] INTEGER PRIMARY KEY,[keyword] text)''')
    con.execute('''CREATE TABLE cpe_list ([key] INTEGER PRIMARY KEY,[cpe] text)''')
    con.commit()
    con.execute("INSERT INTO config (smtp_login,smtp_password,smtpsrv,port,sender, receiver,tls,language) VALUES (?,?,?,?,?,?,?,?);", (smtp_login,enc_pass,smtpsrv,str(port),sender, receiver,tls,language))
    con.commit()         
    github_username = input("Please enter your Github username : ")
    github_api_key = getpass("Please enter your Github API Token : ")
    try:
        login_attempt = requests.get('https://api.github.com/search/repositories?q=github+api', auth=(github_username,github_api_key))
        if login_attempt.status_code != 200:
            raise
        else:
            con.execute("INSERT INTO config (github_api_key,github_username,cvss_alert_limit,no_score_cve_alert) VALUES (?,?,?,?);", (github_username,github_api_key,"no_limit","True"))
            con.commit()
    except:
        print("Github API authentication failed. You can add this config on the web UI after installation...")
    else:
        con.execute("INSERT INTO config (github_api_key,github_username,cvss_alert_limit,no_score_cve_alert) VALUES (?,?,?,?);", ("None","None","no_limit","True"))
        con.commit()
    print()
    username = ""
    password = ""
    password2 = "!="
    while username == "" or password == "" or password != password2:
        username = input("Enter the username that can be used on the Web UI : ")
        password = getpass("Enter the password (please choose a strong password !) : ")
        password2 = getpass("Confirm the password : ")
        if password != password2:
            print("Both passwords must be the same.")
        if username == "":
            print("A username must be filled in.")
        if password == "":
            print("A password must be entered.")        
    con.execute('''CREATE TABLE users ([uid] INTEGER PRIMARY KEY,[username] text,[pass_hash] text)''')
    con.execute('''CREATE TABLE secret_key ([uid] INTEGER PRIMARY KEY,[app_secret_key] text)''')
    con.commit()
    hashed_pwd = generate_password_hash(password, 'sha512')
    cur = con.cursor()
    cur.execute("INSERT INTO users (username, pass_hash) VALUES (?,?);", (username, hashed_pwd))
    con.commit()
    secret_key = os.urandom(2048).hex()
    cur.execute("INSERT INTO secret_key (app_secret_key) VALUES (?);", (secret_key,))
    con.commit()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-sender",nargs=1,required=True,metavar="email-addr",help="set sender email address")
    parser.add_argument("-login",nargs=1,required=True,metavar="smtp_login",help="set SMTP login")
    parser.add_argument("-p",nargs=1,required=True,metavar="smtp_password",help="set sender SMTP password")
    parser.add_argument("-server",nargs=1,required=True,metavar="smtp_server",help="set SMTP server name")
    parser.add_argument("-port",nargs=1,required=True,metavar="port",help="set SMTP port used by the server", type=int)
    parser.add_argument("-tls",nargs=1,required=True,metavar="yes|no",help="use TLS for SMTP authentication")
    parser.add_argument("-r",nargs=1,required=True,metavar="email-addr1;email-addr2",help="set receivers email address")
    parser.add_argument("-lang",nargs=1,required=True,metavar="en|fr",help="set the language of the emails")
    args = parser.parse_args()
    sender = ''.join(args.sender)
    smtp_login = ''.join(args.login)
    smtp_passwd = ''.join(args.p)
    server = ''.join(args.server)
    port = args.port[0]
    tls = ''.join(args.tls)
    receivers = ''.join(args.r)
    language = ''.join(args.lang)
    print("------------------------------------")
    print(f"SECMON setup script - Version {__version__}")
    print("------------------------------------")
    license_validation = input("SECMON is licensed by CC BY-NC-SA 4.0 license. Do you accept the terms of the license? (y/Y;n/N) : ")
    if license_validation == "y" or license_validation == "Y":
        mailTester(smtp_login, smtp_passwd, server, port, tls, sender, receivers, language)
    else:
        print("\nYou must accept the terms of the license to install and use SECMON.")
        exit()
main()
