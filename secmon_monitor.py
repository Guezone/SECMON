""" 
SECMON - Source code of the SECMON monitoring script.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
import base64, os, requests, feedparser, colorama, tweepy, sqlite3
from datetime import datetime
rss_feeds = [ 
	'https://cyware.com/allnews/feed',
	'https://www.cshub.com/rss/categories/attacks',
	'https://www.darkreading.com/rss_simple.asp',
	'https://www.schneier.com/feed/atom/',
	'https://www.cshub.com/rss/categories/threat-defense',
	'https://www.cshub.com/rss/categories/malware',
	'https://www.fortiguard.com/rss/ir.xml',
	'https://nakedsecurity.sophos.com/feed/',
	'https://www.techrepublic.com/rssfeeds/topic/security/?feedType=rssfeeds',
	'http://feeds.feedburner.com/TheHackersNews?format=xml',
	'https://www.cert.ssi.gouv.fr/feed/',
	'https://us-cert.cisa.gov/ncas/all.xml',
	'https://www.zataz.com/feed/',
]
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

sender, receiver, password, smtpsrv, port, tls, keywords = '','','','','','',''
def checkConfig(sender, receiver, password, smtpsrv, port, tls, keywords, dir_path, chk_result):	
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
		print(bcolors.OKGREEN+"1. Configuration is good."+bcolors.ENDC)
		chk_result["1"] = "1. Configuration is good."
	else:
		print(bcolors.FAIL+"1. Error in the config."+bcolors.ENDC)
		chk_result['1'] = "1. Error in the config."


def checkRssFeeds(rss_feeds,dir_path, chk_result):
	try:
		for feed in rss_feeds:
			r = requests.get(feed)
			if int(r.status_code) != 200:
				raise
		print(bcolors.OKGREEN+"2. All RSS feeds are available."+bcolors.ENDC)
		chk_result['2'] = "2. All RSS feeds are available."
	except:
		print(bcolors.FAIL+"2. One or more RSS feeds are unavailable."+bcolors.ENDC)
		chk_result['2'] = "2. One or more RSS feeds are unavailable."
	try:
		feed = "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml"
		r = requests.get(feed)
		if int(r.status_code) != 200:
			raise
		print(bcolors.OKGREEN+"3. NVD RSS feed is available."+bcolors.ENDC)
		chk_result['3'] = "3. NVD RSS feed is available."
	except:
		print(bcolors.FAIL+"4. NVD RSS feed is unavailable."+bcolors.ENDC)
		chk_result['3'] = "3. NVD RSS feed is unavailable."

def checkFileSize(dir_path, chk_result):
	db_path = dir_path+"secmon.db"
	log_file_path = dir_path+"logs.txt"

	try:
		stat = os.stat(db_path)
		size = stat.st_size
		mb_size = round(size / (1024 * 1024), 3)
		if mb_size >= 100.0:
			print(bcolors.WARNING+"4. The database is available but this size is too high."+bcolors.ENDC)
			chk_result['4'] = "4. The database is available but this size is too high."
		else:
			print(bcolors.OKGREEN+"4. The database is available and this size is good."+bcolors.ENDC)
			chk_result['4'] = "4. The database is available and this size is good."
	except:
		print(bcolors.FAIL+"4. The database is unavailable."+bcolors.ENDC)
		chk_result['4'] = "4. The database is unavailable."

	try:
		stat = os.stat(log_file_path)
		size = stat.st_size
		mb_size = round(size / (1024 * 1024), 3)
		if mb_size >= 0.5:
			print(bcolors.WARNING+"5. The size of a log file is too high. Removing log file."+bcolors.ENDC)
			chk_result['5'] = "5. The size of a log file is too high. Removing log file."
			os.remove(log_file_path)
			os.system(f"touch {dir_path}logs.txt && chown www-data:www-data {dir_path}logs.txt")
		else:
			chk_result['5'] = "5. The size of a log file is good."
			print(bcolors.OKGREEN+"5. The size of a log file is good."+bcolors.ENDC)
	except:
		print(bcolors.FAIL+"5. Log file not found."+bcolors.ENDC)
		chk_result['5'] = "5. Log file not found."

def main(dir_path):
	colorama.init()
	print("--------- Monitoring Module --------")
	timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print(bcolors.OKBLUE+" Starting at : "+timestamp+bcolors.ENDC)
	print("------------------------------------")
	chk_result = {'1':'','2':'','3':'','4':'','5':'','6':''}
	checkConfig(sender, receiver, password, smtpsrv, port, tls, keywords, dir_path, chk_result)
	checkRssFeeds(rss_feeds, dir_path, chk_result)
	checkFileSize(dir_path, chk_result)
	print("------------------------------------")
	timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print(bcolors.OKBLUE+" Finished at : "+timestamp+bcolors.ENDC)
	print("------------------------------------")
	return chk_result
if __name__ == "__main__":
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_monitor.py","")
	main(dir_path)
