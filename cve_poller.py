""" 
SECMON - Source code of the SECMON CVE poller script.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
import base64, os, smtplib, re, requests, time, sqlite3, feedparser, colorama, warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from secmon_lib import getParsedCpe, translateText, getUserLanguage, getCpeList, pollCveIdFromCpe, writeCveTypeLog, writeMgmtTasksLog
warnings.filterwarnings("ignore", category=DeprecationWarning) 
sender, receiver, password, smtpsrv, port, tls, keywords = '','','','','','',''
script_path = os.path.abspath(__file__)
dir_path = script_path.replace("cve_poller.py","")
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

def checkConfig(sender, receiver, password, smtpsrv, port, tls,keywords):	
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("cve_poller.py","")
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
		cvePoller(sender, receivers, password, smtpsrv, port, tls, keywords, language)
	else:
		print(bcolors.FAIL+"Error in the config."+bcolors.ENDC)
		exit()

def cvePoller(sender, receivers, password, smtpsrv, port, tls, keywords, language):
	print("------------------------------------")
	summary, url = "",""
	cve_rss = []
	current_feed = feedparser.parse("https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml")
	for entries in current_feed.entries:
		title = entries.title
		summary = entries.summary
		cve_id = re.findall('CVE-\d{4}-\d{4,7}',title)
		cve_id = cve_id[0]
		cve_rss.append(cve_id+"(=)"+summary)
	summary, url = "",""
	con = sqlite3.connect(dir_path+'secmon.db')
	cur = con.cursor()
	dest_language = getUserLanguage()
	now_date = str(datetime.now()).split(" ")[0].split("-")
	idx_date = now_date[2]+"/"+now_date[1]+"/"+now_date[0]


	# CPE
	new_cve_list = []
	cur.execute("SELECT cpe FROM cpe_list")
	db_result_list = cur.fetchall()
	cpes = getCpeList()
	if cpes != []:
		print(bcolors.HEADER+"Polling NVD related to your product list (CPE based search)."+bcolors.ENDC+"\n")
		for cpe in cpes:
			cve_ids = pollCveIdFromCpe(cpe)
			cpe = cpe.replace("\n","").replace(" ","")
			for cve_id in cve_ids:
				cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE CVE_ID = (?);", (cve_id,))
				db_result_list = cur.fetchall()
				db_result_str = ""
				for db_result_tuple in db_result_list:
					for result in db_result_tuple:
						db_result_str+=result
				if cve_id not in db_result_str:
					nvd_base_url = "https://services.nvd.nist.gov/rest/json/cve/1.0/"
					nvd_query = nvd_base_url+cve_id
					nvd_response = requests.get(url=nvd_query)
					nvd_data = nvd_response.json()
					if 'result' in nvd_data.keys():
						if 'reference_data' in nvd_data['result']['CVE_Items'][0]['cve']['references']:
							nvd_links = nvd_data['result']['CVE_Items'][0]['cve']['references']['reference_data']
							cve_sources = ""
							for link in nvd_links:
								cve_sources += (link['url']+"\n")
						else:
								cve_sources = "N/A"
						key_match = cpe		
						cve_score = ""
						fr_society = " (constructeur/éditeur)"
						en_society = " (builder/publisher)"
						if not "impact" in nvd_data['result']['CVE_Items'][0].keys():
							cve_score = "N/A"
							try:	
								webpage = requests.get("https://nvd.nist.gov/vuln/detail/{}".format(cve_id))
								soup = BeautifulSoup(webpage.content, 'html.parser')
								cve_cna_score = soup.find(id='Cvss3CnaCalculatorAnchor')
								cve_cna_score = cve_cna_score.get_text()
								if cve_cna_score != "":
									if language == "fr" or language=="FR":
										cve_score = cve_cna_score + fr_society
									else:
										cve_score = cve_cna_score + en_society
								else:
									cve_score = "N/A"
							except:
									cve_score = "N/A"
						else:
							try:
								cve_score = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['baseScore']
							except:
								cve_score = "N/A"
						published_date = nvd_data['result']['CVE_Items'][0]['publishedDate']
						formatted_date = published_date.split("T")[0]
						formatted_date = datetime.strptime(formatted_date,"%Y-%m-%d")
						date_2_days_ago = datetime.now() - timedelta(days=7)
						if (date_2_days_ago<=formatted_date) and (formatted_date<=datetime.now()):
							cve_date_status = "Potentially new CVE"
						else:
							cve_date_status = "Potentially an update"

						cve_date = published_date.split("T")[0]
						if language == "fr" or language == "FR":
							fr_date = cve_date.split("-")
							cve_date = fr_date[2]+"/"+fr_date[1]+"/"+fr_date[0]
						if (cve_score=="N/A"):
							cve_status = cve_date_status+" - "+"Not yet rated (No score, no CPE)"
						else:
							cve_status = cve_date_status+" - "+"Valid evaluation"
						cve_cpe = ""
						if "configurations" in nvd_data['result']['CVE_Items'][0].keys():
							if nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
								for node in nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
									if 'cpe_match' in node.keys():
										for cpe_node in node['cpe_match']:
											cve_cpe += (cpe_node['cpe23Uri']+'\n')
						if cve_cpe == "":
							cve_cpe = "N/A"
						cve_description = nvd_data['result']['CVE_Items'][0]['cve']['description']['description_data'][0]['value']
						if language == "fr" or language=="FR":
							try:
								cve_description = translateText(dest_language,cve_description)
							except:
								pass
							if not "/" in cve_date:
								cve_date = cve_date.split("-")[2]+"/"+cve_date.split("-")[1]+"/"+cve_date.split("-")[0]
							try:
								cve_status = translateText(dest_language,cve_status).replace("nouveau", "une nouvelle").replace("évalué","évaluée")
							except:
								pass
						nvd_link = 'https://nvd.nist.gov/vuln/detail/'+cve_id
					else:
						cve_description = "N/A"
						date = str(datetime.now()).split(" ")[0].split("-")
						cve_date = date[2]+"/"+date[1]+"/"+date[0]
						cve_score = "N/A"
						cve_sources = "N/A"
						cve_status = "N/A"
						cve_cpe = "N/A"
						nvd_link = 'https://nvd.nist.gov/vuln/detail/'+cve_id						
					status = "Unread"	
					if cve_id not in new_cve_list:
						cur.execute("INSERT INTO CVE_DATA (CVE_ID,KEYWORD,STATUS,CVE_SCORE,CVE_DATE,CVE_DESCRIPTION,CVE_EVAL,CVE_CPE,CVE_SOURCES,EXPLOIT_FIND,INDEXING_DATE) VALUES (?,?,?,?,?,?,?,?,?,?,?);", (cve_id,key_match,status,str(cve_score).split(" ")[0],cve_date,cve_description,cve_status,cve_cpe,cve_sources,"False",idx_date))
						con.commit()
						report="updated"
						print("New CVE detected -> "+cve_id)
						try:	
							sendAlert(sender, password, smtpsrv, port, tls, receivers, cve_id, cve_sources, str(cve_score).split(" ")[0], cve_status, cve_cpe, cve_date, cve_description, language,key_match)
							alert = "sent"
						except:
							alert = "unsent"
						new_cve_list.append(cve_id)
						writeCveTypeLog("cve_poller",cve_id,"new",key_match,str(cve_score).split(" ")[0],cve_date,cve_cpe,report,alert)
	if not new_cve_list:
		print(bcolors.HEADER+"No new CVE related to your (CPE) product list."+bcolors.ENDC)
		print("------------------------------------")
	else:
		timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		print(bcolors.OKGREEN+"Database was updated with new CVE."+bcolors.ENDC)
		print("------------------------------------")

	# RSS
	new_cve_list = []
	print(bcolors.HEADER+"Polling NVD RSS feed (keyword based search)."+bcolors.ENDC+"\n")
	for cve in cve_rss:
		cve_id = cve.split("(=)")[0]
		summary = cve.split("(=)")[1]
		for key in keywords:
			if key in summary: 
				key_match = key
				cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE CVE_ID = (?);", (cve_id,))
				db_result_list = cur.fetchall()
				db_result_str = ""
				for db_result_tuple in db_result_list:
					for result in db_result_tuple:	
						db_result_str+=result
				if cve_id not in db_result_str:
					nvd_base_url = "https://services.nvd.nist.gov/rest/json/cve/1.0/"
					nvd_query = nvd_base_url+cve_id
					nvd_response = requests.get(url=nvd_query)
					nvd_data = nvd_response.json()
					if 'result' in nvd_data.keys():
						if 'reference_data' in nvd_data['result']['CVE_Items'][0]['cve']['references']:
							nvd_links = nvd_data['result']['CVE_Items'][0]['cve']['references']['reference_data']
							cve_sources = ""
							for link in nvd_links:
								cve_sources += (link['url']+"\n")
						else:
								cve_sources = "N/A"
						cve_score = ""
						fr_society = " (constructeur/éditeur)"
						en_society = " (builder/publisher)"
						if not "impact" in nvd_data['result']['CVE_Items'][0].keys():
							cve_score = "N/A"
							try:	
								webpage = requests.get("https://nvd.nist.gov/vuln/detail/{}".format(cve_id))
								soup = BeautifulSoup(webpage.content, 'html.parser')
								cve_cna_score = soup.find(id='Cvss3CnaCalculatorAnchor')
								cve_cna_score = cve_cna_score.get_text()
								if cve_cna_score != "":
									if language == "fr" or language=="FR":
										cve_score = cve_cna_score + fr_society
									else:
										cve_score = cve_cna_score + en_society
								else:
									cve_score = "N/A"
							except:
									cve_score = "N/A"
						else:
							try:
								cve_score = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['baseScore']
							except:
								cve_score = "N/A"
						published_date = nvd_data['result']['CVE_Items'][0]['publishedDate']
						formatted_date = published_date.split("T")[0]
						formatted_date = datetime.strptime(formatted_date,"%Y-%m-%d")
						date_2_days_ago = datetime.now() - timedelta(days=7)
						if (date_2_days_ago<=formatted_date) and (formatted_date<=datetime.now()):
							cve_date_status = "Potentially new CVE"
						else:
							cve_date_status = "Potentially an update"

						cve_date = published_date.split("T")[0]
						if language == "fr" or language == "FR":
							fr_date = cve_date.split("-")
							cve_date = fr_date[2]+"/"+fr_date[1]+"/"+fr_date[0]
						if (cve_score=="N/A"):
							cve_status = cve_date_status+" - "+"Not yet rated (No score, no CPE)"
						else:
							cve_status = cve_date_status+" - "+"Valid evaluation"
						cve_cpe = ""
						if "configurations" in nvd_data['result']['CVE_Items'][0].keys():
							if nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
								for node in nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
									if 'cpe_match' in node.keys():
										for cpe_node in node['cpe_match']:
											cve_cpe += (cpe_node['cpe23Uri']+'\n')
						if cve_cpe == "":
							cve_cpe = "N/A"
						cve_description = nvd_data['result']['CVE_Items'][0]['cve']['description']['description_data'][0]['value']
						nvd_link = 'https://nvd.nist.gov/vuln/detail/'+cve_id
						if language == "fr" or language=="FR":
							try:
								cve_description = translateText(dest_language,cve_description)
							except:
								pass
							if not "/" in cve_date:
								cve_date = cve_date.split("-")[2]+"/"+cve_date.split("-")[1]+"/"+cve_date.split("-")[0]
							try:	
								cve_status = translateText(dest_language,cve_status).replace("nouveau", "une nouvelle").replace("évalué","évaluée")	
							except:
								pass
					else:
						cve_description = summary
						date = str(datetime.now()).split(" ")[0].split("-")
						cve_date = date[2]+"/"+date[1]+"/"+date[0]
						cve_score = "N/A"
						cve_sources = "N/A"
						cve_status = "N/A"
						cve_cpe = "N/A"
						nvd_link = 'https://nvd.nist.gov/vuln/detail/'+cve_id					
					status = "Unread"
					if cve_id not in new_cve_list:
						cur.execute("INSERT INTO CVE_DATA (CVE_ID,KEYWORD,STATUS,CVE_SCORE,CVE_DATE,CVE_DESCRIPTION,CVE_EVAL,CVE_CPE,CVE_SOURCES,EXPLOIT_FIND,INDEXING_DATE) VALUES (?,?,?,?,?,?,?,?,?,?,?);", (cve_id,key_match,status,str(cve_score).split(" ")[0],cve_date,cve_description,cve_status,cve_cpe,cve_sources,"False",idx_date))
						con.commit()
						print("New CVE detected -> "+cve_id)
						report="updated"
						try:	
							sendAlert(sender, password, smtpsrv, port, tls, receivers, cve_id, cve_sources, str(cve_score).split(" ")[0], cve_status, cve_cpe, cve_date, cve_description, language,key_match)
							alert = "sent"
						except:
							alert = "unsent"
						new_cve_list.append(cve_id)
						writeCveTypeLog("cve_poller",cve_id,"new",key_match,str(cve_score).split(" ")[0],cve_date,cve_cpe,report,alert)
							
	if not new_cve_list:
		print(bcolors.HEADER+"No new CVE matched with your keyword list."+bcolors.ENDC)	
		print("------------------------------------")
		timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		print(bcolors.OKBLUE+"Finished at : "+timestamp+bcolors.ENDC)
		print("------------------------------------")

	else:
		print(bcolors.OKGREEN+"Database was updated with new CVE."+bcolors.ENDC)
		timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		print("------------------------------------")
		print(bcolors.OKBLUE+"Finished at : "+timestamp+bcolors.ENDC)
		print("------------------------------------")

def sendAlert(sender, password, smtpsrv, port, tls, receivers, cve_id, cve_sources, cve_score, cve_status, cve_cpe, cve_date, cve_description, language,key_match):
	body = ""
	nvd_url = "https://nvd.nist.gov/vuln/detail/"+cve_id
	for receiver in receivers:
		with open(dir_path+'cve_template.html', 'r') as template:
			html_code = template.read()
			if "cpe" in key_match:
				key_match = getParsedCpe(key_match)
			if language == "fr" or language=="FR":
				html_code = html_code.replace("Responsive HTML email templates","Alerte")
				html_code = html_code.replace("$CVE",cve_id+" (Produit : {})".format(key_match))
				try:
					cve_description = translateText(dest_language,cve_description)
				except:
					pass
				html_code = html_code.replace("$DESCRIPTION", cve_description.replace("u'","").replace("u ``",""))
				if not "/" in cve_date:
					cve_date = cve_date.split("-")[2]+"/"+cve_date.split("-")[1]+"/"+cve_date.split("-")[0]
				html_code = html_code.replace("$DATE", cve_date)
				html_code = html_code.replace("$SCORE", str(cve_score))
				try:
					cve_status = translateText(dest_language,cve_status).replace("nouveau", "une nouvelle").replace("évalué","évaluée")
				except:
					pass
				html_code = html_code.replace("$STATUS", cve_status)
				html_code = html_code.replace("$CPE", cve_cpe)
				html_code = html_code.replace("$SOURCES", cve_sources)
				html_code = html_code.replace("See more details", "Voir plus de détails")
				html_code = html_code.replace("Publication date", "Date de publication")
				html_code = html_code.replace("Status", "Statut")
				html_code = html_code.replace("CPE/Product", "CPE/Produit")
				html_code = html_code.replace("CVSS Score (V3)", "Score CVSS (V3)")
				html_code = html_code.replace("This email was sent by", "Cet email a été envoyé par")
				html_code = html_code.replace("CVE module", "Module CVE")
				body = html_code.replace("URL OF THE NEWS",nvd_url)
			else:
				html_code = html_code.replace("Responsive HTML email templates","Alert")
				html_code = html_code.replace("$CVE",cve_id+" (Product : {})".format(key_match))
				html_code = html_code.replace("$DESCRIPTION", cve_description.replace("u'","").replace("u ``",""))
				html_code = html_code.replace("$DATE", cve_date)
				html_code = html_code.replace("$SCORE", str(cve_score))
				html_code = html_code.replace("$STATUS", cve_status)
				html_code = html_code.replace("$CPE", cve_cpe)
				html_code = html_code.replace("$SOURCES", cve_sources)
				body = html_code.replace("URL OF THE NEWS",nvd_url)
		print(bcolors.HEADER+"Sending alert at {}...".format(receiver)+bcolors.ENDC)
		try:
			smtpserver = smtplib.SMTP(smtpsrv,port)
			msg = MIMEMultipart()
			msg['Subject'] = 'SECMON - CVE'
			msg['From'] = sender
			msg['To'] = receiver
			msg.attach(MIMEText(body, 'html'))
		except:
			print(bcolors.FAIL+"Failed to send alert at {}.".format(receiver)+bcolors.ENDC)
			exit()
		try:
			if tls == "yes":
				smtpserver.ehlo()
				smtpserver.starttls()
				smtpserver.login(sender, password)
				smtpserver.sendmail(sender, receiver, msg.as_string())
				print(bcolors.HEADER+"Alert was sent at {}\n".format(receiver)+bcolors.ENDC)
			elif tls == "no":
				smtpserver.login(sender, password)
				smtpserver.sendmail(sender, receiver, msg.as_string())
				print(bcolors.HEADER+"Alert was sent at {}\n".format(receiver)+bcolors.ENDC)
		except Exception as e:
			print(bcolors.FAIL+"An error occurred during authentication with the SMTP server. Check the configuration and try again."+bcolors.ENDC)
			exit()

def main():
	colorama.init()
	print("------------ CVE Module ------------")
	timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print(bcolors.OKBLUE+"Starting at : "+timestamp+bcolors.ENDC)
	print("------------------------------------")
	checkConfig(sender, receiver, password, smtpsrv, port, tls, keywords)
	
main()


