""" 
SECMON - Source code of the SECMON rss poller script.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
import base64, os, smtplib, re, requests, sqlite3, feedparser, colorama
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from datetime import datetime, timedelta
from secmon_lib import translateText, getUserLanguage, writeMgmtTasksLog, writeNewRssNewLog
rss_feeds = [ 
	'https://cyware.com/allnews/feed',
	'https://www.cshub.com/rss/categories/attacks',
	'https://www.schneier.com/feed/atom/',
	'https://www.cshub.com/rss/categories/threat-defense',
	'https://www.cshub.com/rss/categories/malware',
	'https://www.fortiguard.com/rss/ir.xml',
	'https://nakedsecurity.sophos.com/feed/',
	'https://www.techrepublic.com/rssfeeds/topic/security/?feedType=rssfeeds',
	'https://www.cert.ssi.gouv.fr/feed/',
	'https://us-cert.cisa.gov/ncas/all.xml',
	'https://www.zataz.com/feed/',
]
sender, receiver, password, smtpsrv, port, tls, keywords = '','','','','','',''
script_path = os.path.abspath(__file__)
dir_path = script_path.replace("rss_poller.py","")
log_file = dir_path+"logs.txt"
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
def parseRSSSource(source):
	if "us-cert.cisa" in source or "cyware.com" in source:
		new_source = source.replace("https://","").split(".")[0]
	else:
		new_source = source.replace("https://","").replace("www.","").split(".")[0]
	return new_source
	
def checkConfig(sender, receiver, password, smtpsrv, port, tls,rss_feeds):	
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("rss_poller.py","")
	con = sqlite3.connect(dir_path+'secmon.db')
	cur = con.cursor()
	cur.execute("SELECT sender FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		sender = value

	cur.execute("SELECT password FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		b = value.encode("UTF-8")
		bytes_password = base64.b64decode(b)
		password = bytes_password.decode("UTF-8")

	cur.execute("SELECT smtpsrv FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		smtpsrv = value

	cur.execute("SELECT port FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		port = value

	cur.execute("SELECT receiver FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		receivers = value.split(";")

	cur.execute("SELECT tls FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		tls = value

	cur.execute("SELECT language FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		language = value

	cur.execute("SELECT receiver FROM config")
	db_result_tuple = cur.fetchone()
	for value in db_result_tuple:
		receivers = value.split(";")
	
	cur.execute("SELECT keyword FROM keyword_list")
	db_result_list = cur.fetchall()
	keywords = []
	for db_result_tuple in db_result_list:
		for result in db_result_tuple:	
			keywords.append(result)


	if all(value != '' for value in [sender, receivers, password, smtpsrv, str(port), tls, language]):
		print(bcolors.OKGREEN+"Configuration is good."+bcolors.ENDC)
		rssPoller(sender, receivers, password, smtpsrv, port, tls, language, rss_feeds)
	else:
		print(bcolors.FAIL+"Error in the config."+bcolors.ENDC)

def rssPoller(sender, receivers, password, smtpsrv, port, tls, language, rss_feeds):
	print("------------------------------------")
	summary, url = "",""
	new = False
	con = sqlite3.connect(dir_path+'secmon.db')
	cur = con.cursor()
	for rss_feed in rss_feeds:
		current_feed = feedparser.parse(rss_feed)
		for entries in current_feed.entries:
			url = entries.link
			cur.execute("SELECT RSS_URL FROM RSS_DATA WHERE RSS_URL = (?);", (url,))
			db_result_list = cur.fetchall()
			db_result_str = ""
			for db_result_tuple in db_result_list:
				for result in db_result_tuple:	
					db_result_str+=result
			if url not in db_result_str:
				new = True
				title = entries.title
				summary = entries.summary
				if summary == "":
					summary+="Empty summary."
				dest_language = getUserLanguage()
				try:
					title = translateText(dest_language,title)
					summary = translateText(dest_language,summary)
				except:
					pass

				cur.execute("INSERT INTO RSS_DATA (RSS_URL, title, rss_f, summary) VALUES (?,?,?,?);", (url,title,rss_feed,summary))
				con.commit()
				try:
					sendAlert(sender, password, smtpsrv, port, tls, receivers, title, summary, url, language, rss_feed)
					mail = "sent"
				except:
					mail = "unsent"
				writeNewRssNewLog("rss_poller",parseRSSSource(rss_feed),rss_feed,title,url,mail)
	if new == True:
		print(bcolors.OKGREEN+"Database was updated. Goodbye."+bcolors.ENDC)
	else:
		print(bcolors.OKGREEN+"No news. Goodbye."+bcolors.ENDC)
	print("------------------------------------")
	timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print(bcolors.OKBLUE+"Finished at : "+timestamp+bcolors.ENDC)
	print("------------------------------------")

def sendAlert(sender, password, smtpsrv, port, tls, receivers, title, summary, url, language, rss_feed):
	body = ""
	for receiver in receivers:
		with open(dir_path+'rss_template.html', 'r') as template:
			html_code = template.read()
			html_code = html_code.replace("$SOURCE", parseRSSSource(rss_feed))
			if language == "fr" or language=="FR":
				html_code = html_code.replace("See more details", "Voir plus de détails")
				html_code = html_code.replace("This email was sent by", "Cet email a été envoyé par")
				html_code = html_code.replace("Notification", "Information")
				html_code = html_code.replace("RSS module", "Module RSS")
				html_code = html_code.replace("$TITLE", title)
				html_code = html_code.replace("$SUMMARY", summary)
				html_code = html_code.replace("Title", "Titre")
				html_code = html_code.replace("Summary", "Résumé")
				body = html_code.replace("URL OF THE NEWS",url)
			else:
				html_code = html_code.replace("$TITLE", title)
				html_code = html_code.replace("Notification", "News")
				html_code = html_code.replace("$SUMMARY", summary)
				body = html_code.replace("URL OF THE NEWS",url)
		print(bcolors.HEADER+"Sending news at {}...".format(receiver)+bcolors.ENDC)
		try:
			smtpserver = smtplib.SMTP(smtpsrv,port)
			msg = MIMEMultipart()
			msg['Subject'] = 'SECMON - RSS'
			msg['From'] = sender
			msg['To'] = receiver
			msg.attach(MIMEText(body, 'html'))
		except:
			print(bcolors.FAIL+"Failed to send news at {}.".format(receiver)+bcolors.ENDC)
			exit()
		try:
			if tls == "yes":
				smtpserver.ehlo()
				smtpserver.starttls()
				smtpserver.login(sender, password)
				smtpserver.sendmail(sender, receiver, msg.as_string())
				print(bcolors.HEADER+"News was sent at {}\n".format(receiver)+bcolors.ENDC)
			elif tls == "no":
				smtpserver.login(sender, password)
				smtpserver.sendmail(sender, receiver, msg.as_string())
				print(bcolors.HEADER+"News was sent at {}\n".format(receiver)+bcolors.ENDC)
		except Exception as e:
			print(bcolors.FAIL+"An error occurred during authentication with the SMTP server. Check the configuration and try again."+bcolors.ENDC)
			exit()

def main():
	print()
	colorama.init()
	print("------------ RSS Module ------------")
	timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print(bcolors.OKBLUE+"Starting at : "+timestamp+bcolors.ENDC)
	print("------------------------------------")
	checkConfig(sender, receiver, password, smtpsrv, port, tls,rss_feeds)
	
main()


