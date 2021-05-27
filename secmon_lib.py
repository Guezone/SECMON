""" 
SECMON - Library for SECMON python web backend.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.0"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
from flask import Flask, url_for, render_template, send_from_directory, request, flash, redirect, safe_join, session, url_for, session, abort
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Color, Alignment, Border, Side, colors, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import ColumnDimension
from deep_translator import GoogleTranslator, MyMemoryTranslator
import jinja2.exceptions, sqlite3,requests, feedparser, re, smtplib, os, tweepy, base64, time, socket, random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import sqlalchemy, SQLAlchemy
from flask_simplelogin import is_logged_in
from bs4 import BeautifulSoup
import cve_searchsploit as CS
import secmon_monitor,traceback
from multiprocessing import Process, Queue
from datetime import *
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
messages = {
    'login_success': 'Login success.',
    'login_failure': 'Bad Username, bad password or bad request.',
    'logout': 'You have been successfully logged out.',
    'login_required': 'Please sign-in.',
    'access_denied': 'Access denied.',
    'auth_error': 'Error： {0}'
}
def handleException(error):
    now = datetime.now()
    now = now.strftime("%d/%m/%Y, %H:%M:%S")
    print(f"################## NEW SCRIPT ERROR AT {now} ##################")
    print(traceback.print_exc())
    print("################## PLEASE REPORT THIS ON GITHUB ##################")
def generateCveReport(start_date,end_date,isFull):
    bold_font = Font(bold=True,color='00FAAA3C', size=14)
    grey = Color(rgb='00202020')
    center_aligned_text = Alignment(horizontal="center")
    wrapped_text = Alignment(horizontal="center",wrapText=True,shrinkToFit=True,vertical="center")
    thin_border = Side(border_style="thin")
    square_border = Border(top=thin_border,right=thin_border,bottom=thin_border,left=thin_border)
    title_bg = PatternFill(fill_type = "solid",fgColor=grey)
    fr = [
    'ID CVE',
    'Produit matché',
    'Description',
    'Date de publication',
    'Score CVSS',
    'Sources',
    'Statut',
    'Produits affectés']
    en = [
    'CVE ID',
    'Matching product',
    'Summary',
    'Published date',
    'CVSS Score',
    'Sources',
    'Status',
    'Affected products']
    cols = ["A","B","C","D","E","F","G","H"]
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")  
    xlsx_report = Workbook()
    sheet = xlsx_report.active
    sheet.title = "Global"
    lang = getUserLanguage()
    sheet.column_dimensions['A'].width = 21
    sheet.column_dimensions['B'].width = 58
    sheet.column_dimensions['C'].width = 73
    sheet.column_dimensions['D'].width = 15
    sheet.column_dimensions['E'].width = 10
    sheet.column_dimensions['F'].width = 110
    sheet.column_dimensions['G'].width = 20
    sheet.column_dimensions['H'].width = 68
    sheet.auto_filter.ref = sheet.dimensions
    i = 0
    while i != 8:
        if lang == "fr":
            letter = cols[i]
            sheet["{}1".format(letter)].font = bold_font
            sheet["{}1".format(letter)].alignment = center_aligned_text
            sheet["{}1".format(letter)].border = square_border
            sheet["{}1".format(letter)].fill = title_bg
            sheet["{}1".format(letter)].value = fr[i]
            i+=1
        else:
            sheet["{}1".format(letter)].font = bold_font
            sheet["{}1".format(letter)].alignment = center_aligned_text
            sheet["{}1".format(letter)].border = square_border
            sheet["{}1".format(letter)].fill = title_bg
            sheet["{}1".format(letter)].value = en[i]            
    cves = []
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    cur.execute("SELECT CVE_ID,KEYWORD,CVE_DESCRIPTION,CVE_DATE,CVE_SCORE,CVE_SOURCES,STATUS,CVE_CPE,INDEXING_DATE FROM CVE_DATA")
    db_result_list = cur.fetchall()
    cves = []
    for db_result_tuple in db_result_list:
        current_cve = []
        for result in db_result_tuple:
            current_cve.append(result)
        cves.append(current_cve)
    for cve in cves:
        cve_date = datetime.strptime(cve[8], "%d/%m/%Y")
        if start_date <= cve_date <= end_date or isFull:
            match = cve[1]
            if "cpe" in match:
                match = getParsedCpe(match)
            cve[1] = match
            cpes = cve[7]
            new_product_list = ""
            if "cpe" in cpes:
                cpe_list = cpes.split("\n")
                for cpe in cpe_list:
                    if "cpe" in cpe:
                        hname = getParsedCpe(cpe)
                        new_product_list+=(hname+"\n")
            if new_product_list == "" or new_product_list == " ":
                new_product_list = "N/A"
            cve[7] = new_product_list
            sheet.append(cve[:-1])
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = wrapped_text

    xlsx_report.save(filename=dir_path+"SECMON-CVE-Report.xlsx")
def writeCveTypeLog(source_script,cve_id,temporal_type,matched_product,cvss_score,cve_date,cpes,report,alert,*args):
    server = socket.gethostbyname(socket.gethostname())
    if cvss_score != "N/A" and cvss_score != "":
        if 0 < float(cvss_score) <= 3.9:
            severity = "Low"
        elif 4.0 < float(cvss_score) <= 6.9:
            severity = "Medium"
        elif 7.0 < float(cvss_score) <= 8.9:
            severity = "High"
        elif 9.0 < float(cvss_score) <= 10:
            severity = "Critical"
        elif cvss_score == "N/A":
            severity = "N/A"
    else:
        severity = "N/A"
    timestamp = datetime.now().isoformat()
    if temporal_type == "new":
        message = f"The {cve_id} has been added."
    else:
        message = f"The {cve_id} has been updated."
    for arg in args:
        message+=arg

    cpes = cpes.replace("\n","+")

    log = f"""{timestamp} source_script="{source_script}" server="{server}" cve_id="{cve_id}" type="{temporal_type}" matched_product="{matched_product}" cvss_score="{cvss_score}" severity="{severity}" cve_date="{cve_date}" cpes="{cpes}" report="{report}" alert="{alert}" message="{message}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log.replace('+" report=','" report='))
        
def writeNewExploitFoundLog(source_script,exploit_source,cve,message):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname())
    log = f"""{timestamp} source_script="{source_script}" server="{server}" cve="{cve}" exploit_source="{exploit_source}" message="{message}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)

def writeNewHighRiskProductLog(source_script,cpe,message):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname())
    if "cpe" in cpe:
        hname = getParsedCpe(cpe)
    else:
        hname = cpe
    log = f"""{timestamp} source_script="{source_script}" server="{server}" cpe="{cpe}" hname="{hname}" message="{message}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)
def writeAuthLog(source_script,username,auth_status,msg,src_ip):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname())
    log = f"""{timestamp} source_script="{source_script}" server="{server}" src_ip="{src_ip}" username="{username}" auth_status="{auth_status}" message="{msg}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)
def getTasks():
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    logfile = dir_path+"logs.txt"
    count = 0
    tid = []
    if os.path.isfile(logfile) == True:
        for line in reversed(list(open(logfile))):
            if "task_id" in line:
                timestamp = line.split(" ")[0]
                formatted_date = datetime.fromisoformat(timestamp)
                date_2_days_ago = datetime.now() - timedelta(hours=2)
                if (date_2_days_ago<=formatted_date) and (formatted_date<=datetime.now()):
                    task_id = line.split('"')[5]
                    if task_id not in tid:
                        tid.append(task_id)
    tasks = []
    for task in tid:
        status = ""
        operation = ""
        if os.path.isfile(logfile) == True:
            for line in reversed(list(open(logfile))):
                if f'task_id="{task}"' in line and "loaded" in line:
                    operation += line.split('"')[9].replace("....",".")
                elif f'task_id="{task}"' in line and "failed" in line:
                    status += "Failed"
                elif f'task_id="{task}"' in line and "success" in line:
                    status += "Success"
            if status =="":
                status="In progress"
        tasks.append([task,operation,status])
    return tasks
def writeTaskLog(source_script,task_id,task_status,message):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname())
    log = f"""{timestamp} source_script="{source_script}" server="{server}" task_id="{task_id}" task_status="{task_status}" message="{message}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)

def writeMgmtTasksLog(source_script,message):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname())
    log = f"""{timestamp} source_script="{source_script}" server="{server}" message="{message}" \n"""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)


def writeNewRssNewLog(source_script,feed,feed_url,news_title,news_url,mail):
    timestamp = datetime.now().isoformat()
    server = socket.gethostbyname(socket.gethostname()) 
    log = f"""{timestamp} source_script="{source_script}" server="{server}" feed="{feed}" feed_url="{feed_url}" news_title="{news_title}" news_url="{news_url}" mail="{mail}" \n"""   
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace(os.path.basename(__file__),"")
    log_file = dir_path+"logs.txt"
    with open(log_file, "a") as f:
        f.write(log)
def translateText(lang,text):
    try:
        translation = GoogleTranslator(source='auto', target=lang).translate(text=text)
        return translation
    except Exception as e:
        handleException(e)
        try:
            translation = MyMemoryTranslator(source='auto', target=lang).translate(text)
            return translation
        except Exception as e:
            handleException(e)
            return text +" (TRANSLATION FAILED)"

def getGithubAPISettings():
    key,username = "",""
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    cur.execute("SELECT github_api_key FROM config")
    db_result_tuple = cur.fetchone()
    for value in db_result_tuple:
        key = value
    cur.execute("SELECT github_username FROM config")
    db_result_tuple = cur.fetchone()
    for value in db_result_tuple:
        username = value
    return key,username

def getUserLanguage():
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    cur.execute("SELECT language FROM config")
    db_result_tuple = cur.fetchone()
    for value in db_result_tuple:
        language = value
    return language
def searchExploit(cve, sleeping):
    exploits = CS.edbid_from_cve(cve)
    result = []
    for exploit in exploits: 
        current_exploit = []
        exploitdb_url = "https://www.exploit-db.com/exploits/"+str(exploit)
        r = requests.get(exploitdb_url,headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text,"html.parser")
        exploit_infos = soup.find_all(class_="stats-title")
        eID = exploit_infos[0].get_text().replace(" ","").replace("\n","")
        eAuthor = exploit_infos[2].get_text().replace(" ","").replace("\n","")
        eType = exploit_infos[3].get_text().replace(" ","").replace("\n","")
        ePlatform = exploit_infos[4].get_text().replace(" ","").replace("\n","")
        eDate = exploit_infos[5].get_text().replace(" ","").replace("\n","")

        current_exploit.append(eID)
        current_exploit.append(exploitdb_url)
        current_exploit.append(eAuthor)
        current_exploit.append(eType)
        current_exploit.append(ePlatform)
        created_date = eDate.split("-")
        current_exploit.append(created_date[2]+"/"+created_date[1]+"/"+created_date[0])
        current_exploit.append("Exploit-DB")
        result.append(current_exploit)
    github_query = "https://api.github.com/search/repositories?q=exploit+"+cve
    github_response = requests.get(url=github_query)
    github_data = github_response.json()
    if sleep == True:
        if "message" in github_data.keys():
            sleep(60)
    if "items" in github_data.keys():
        for exploit in github_data['items']:
            current_exploit = []
            current_exploit.append(exploit["id"])
            current_exploit.append(exploit["html_url"])
            current_exploit.append(exploit["owner"]["login"])
            current_exploit.append("N/A")
            current_exploit.append("N/A")
            created_date = exploit["created_at"].split("T")[0].split("-")
            current_exploit.append(created_date[2]+"/"+created_date[1]+"/"+created_date[0])
            current_exploit.append("Github")
            result.append(current_exploit)
    return result
def pollCveIdFromCpe(cpe):
    cve_ids = []
    if "cpe" in cpe:
        try:
            nvd_query = "https://services.nvd.nist.gov/rest/json/cves/1.0?cpeMatchString="+cpe+"&resultsPerPage=1000"
            nvd_response = requests.get(url=nvd_query)
            nvd_data = nvd_response.json()
            for cve in nvd_data["result"]["CVE_Items"]:
                cve_id = cve["cve"]["CVE_data_meta"]["ID"]
                if cve_id not in cve_ids:
                    cve_ids.append(cve_id)
            result_nb = int(nvd_response.json()['totalResults'])
            current_result = 1000
            page = 1
            while current_result < result_nb:
                page+=1
                nvd_query = "https://services.nvd.nist.gov/rest/json/cves/1.0?cpeMatchString="+cpe+"&resultsPerPage=1000"+f"&startIndex={current_result}"
                nvd_response = requests.get(url=nvd_query)
                nvd_data = nvd_response.json()
                for cve in nvd_data["result"]["CVE_Items"]:
                    cve_id = cve["cve"]["CVE_data_meta"]["ID"]
                    if cve_id not in cve_ids:
                        cve_ids.append(cve_id)
                current_result+=1000
        except Exception as e:
            print("Unable to poll CVE related to :",cpe)
            handleException(e)
            pass
    else:
        cve_rss = []
        current_feed = feedparser.parse("https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml")
        for entries in current_feed.entries:
            title = entries.title
            summary = entries.summary
            cve_id = re.findall('CVE-\d{4}-\d{4,7}',title)
            cve_id = cve_id[0]
            cve_rss.append(cve_id+"(=)"+summary)
        for cve in cve_rss:
            cve_summary = cve.split("(=)")[1]
            cve_id = cve.split("(=)")[0]
            if cpe in cve_summary:
               cve_ids.append(cve_id)
    return cve_ids

def getSecretKey():
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    db_result = cur.execute("SELECT app_secret_key FROM secret_key")
    for data in db_result:
        secret_key = data[0]
    return secret_key

def getHighRiskProducts(dentype):
    if dentype == "hname": 
        critical_products = []
        conn = get_db_connection()
        db_result = conn.execute('SELECT hname FROM high_risk_products',).fetchall()
        for result in db_result:
            current_products = []
            for tuples in result:
                critical_products.append(tuples)
    elif dentype == "cpe": 
        critical_products = []
        conn = get_db_connection()
        db_result = conn.execute('SELECT cpe FROM high_risk_products',).fetchall()
        for result in db_result:
            current_products = []
            for tuples in result:
                critical_products.append(tuples)
    elif dentype == "all": 
        critical_products = []
        conn = get_db_connection()
        db_result = conn.execute('SELECT cpe,hname FROM high_risk_products',).fetchall()
        for result in db_result:
            current_product = []
            for tuples in result:
                current_product.append(tuples)
                if len(current_product) == 2:
                    critical_products.append(current_product)
                    continue
    return critical_products

def returnUsername():
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    username = ""
    db_result = cur.execute("SELECT username FROM users")
    for data in db_result:
        for users in data:
            username = users
    if is_logged_in(username):
        return username
    else:
        return "Not logged !!!"
def deleteProduct(ptype, key_or_cpe):    
    if ptype == "CPE":
        high_risk_products = getHighRiskProducts("cpe")
        if key_or_cpe in high_risk_products:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM high_risk_products WHERE cpe = (?);", (key_or_cpe,))
            con.commit()  
        con = get_db_connection()
        cur = con.cursor()
        try:
            cpelist = []
            cur.execute("SELECT cpe FROM cpe_list")
            db_result_list = cur.fetchall()
            for db_result_tuple in db_result_list:
                for result in db_result_tuple:  
                    cpelist.append(result)
            if key_or_cpe not in cpelist:
                raise
            if not "cpe" in key_or_cpe:
                raise
            cur.execute("DELETE FROM cpe_list WHERE cpe = (?);", (key_or_cpe,))
            cur.execute("DELETE FROM CVE_DATA WHERE KEYWORD = (?);", (key_or_cpe,))
            con.commit()
            return "OK"
        except:
            return "NOK"
    else:
        con = get_db_connection()
        cur = con.cursor()
        try:
            keylist = []
            cur.execute("SELECT keyword FROM keyword_list")
            db_result_list = cur.fetchall()
            for db_result_tuple in db_result_list:
                for result in db_result_tuple:  
                    keylist.append(result)
            if key_or_cpe not in keylist:
                raise
            cur.execute("DELETE FROM keyword_list WHERE keyword = (?);", (key_or_cpe,))
            cur.execute("DELETE FROM CVE_DATA WHERE KEYWORD = (?);", (key_or_cpe,))
            con.commit()
            return "OK"
        except:
            return "NOK"
def registerNewCve(cve_id,reason,product):
    try:
        now_date = str(datetime.now()).split(" ")[0].split("-")
        idx_date = now_date[2]+"/"+now_date[1]+"/"+now_date[0]
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT language FROM config")
        db_result_tuple = cur.fetchone()
        for value in db_result_tuple:
            language = value
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
                if not "impact" in nvd_data['result']['CVE_Items'][0].keys():
                    cve_score = "N/A"
                    try:    
                        webpage = requests.get("https://nvd.nist.gov/vuln/detail/{}".format(cve_id))
                        soup = BeautifulSoup(webpage.content, 'html.parser')
                        cve_cna_score = soup.find(id='Cvss3CnaCalculatorAnchor')
                        cve_cna_score = cve_cna_score.get_text()
                        if cve_cna_score != "":
                            cve_score = cve_cna_score
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
                cve_description = nvd_data['result']['CVE_Items'][0]['cve']['description']['description_data'][0]['value']
                cve_cpe = ""
                if "configurations" in nvd_data['result']['CVE_Items'][0].keys():
                    if nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
                        for node in nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
                            if 'cpe_match' in node.keys():
                                for cpe_node in node['cpe_match']:
                                    cve_cpe += (cpe_node['cpe23Uri']+'\n')
            else:
                cve_score = "N/A"
                cve_date = "N/A"
                cve_cpe = "N/A"

            if cve_cpe == "":
                cve_cpe = "N/A"
            key_match = product
            if reason == "NewProduct":  
                status = "Found when the product was added."
            elif reason == "NewPolling":
                status = "Unread"
            elif reason == "Setup":
                status = "Native"        
            cur.execute("INSERT INTO CVE_DATA (CVE_ID,KEYWORD,STATUS,CVE_SCORE,CVE_DATE,CVE_DESCRIPTION,CVE_EVAL,CVE_CPE,CVE_SOURCES,EXPLOIT_FIND,INDEXING_DATE) VALUES (?,?,?,?,?,?,?,?,?,?,?);", (cve_id,key_match,status,str(cve_score),cve_date,cve_description,cve_status,cve_cpe,cve_sources,"False",idx_date))
            con.commit()
            return "ok"
        else:
            return "already"
    except Exception as e:
        print("ERROR")
        handleException(e)
def addProduct(ptype, key_or_cpe):
    task_id = random.randint(10000,99999)
    writeTaskLog("secmon_web",task_id,"loaded",f"Adding the following product : {key_or_cpe}....")
    if ptype == "CPE":
        con = get_db_connection()
        cur = con.cursor()
        try:
            cpe = key_or_cpe
            cve_ids = pollCveIdFromCpe(cpe)
            for cve_id in cve_ids:
                try:
                    registerNewCve(cve_id,"NewProduct",cpe)
                except Exception as e:
                    handleException(e)
                    pass
            cpelist = []
            cur.execute("SELECT cpe FROM cpe_list")
            db_result_list = cur.fetchall()
            for db_result_tuple in db_result_list:
                for result in db_result_tuple:  
                    cpelist.append(result)
            if key_or_cpe in cpelist:
                raise Exception('Product already in the product list.')
            if not "cpe" in key_or_cpe:
                raise Exception('The CPE is in a bad format.')         
            cur.execute("INSERT INTO cpe_list (cpe) VALUES (?);", (key_or_cpe,))
            con.commit()
            writeTaskLog("secmon_web",task_id,"success",f"Following product successfully added : {key_or_cpe} !")        

        except Exception as e:
            handleException(e)
            writeTaskLog("secmon_web",task_id,"failed",f"Unable to add this product : {key_or_cpe}. {str(e)}.") 
    else:
        con = get_db_connection()
        cur = con.cursor()
        try:
            key = key_or_cpe
            cve_ids = pollCveIdFromCpe(key)
            for cve_id in cve_ids:
                try:
                    registerNewCve(cve_id,"NewProduct",key)
                except Exception as e:
                    handleException(e)
                    pass
            keylist = []
            cur.execute("SELECT keyword FROM keyword_list")
            db_result_list = cur.fetchall()
            for db_result_tuple in db_result_list:
                for result in db_result_tuple:  
                    keylist.append(result)
            if key_or_cpe in keylist:
                 raise Exception('Product already exist ! ')
            cur.execute("INSERT INTO keyword_list (keyword) VALUES (?);", (key_or_cpe,))
            con.commit()
            writeTaskLog("secmon_web",task_id,"success",f"Following product successfully added : {key_or_cpe} !") 
            return "OK"
        except Exception as e:
            handleException(e)
            writeTaskLog("secmon_web",task_id,"failed",f"Unable to add this product : {key_or_cpe}. {str(e)}.") 
            return "NOK"
def getProductsStats():
    product_number = 0
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT keyword FROM keyword_list")
    db_result_list = cur.fetchall()
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:  
            product_number+=1
    cur.execute("SELECT cpe FROM cpe_list")
    db_result_list = cur.fetchall()
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:  
            product_number+=1
    return product_number
def getCveByProduct(product,sleeping):
    con = get_db_connection()
    cur = con.cursor()
    if "cpe" in product:
        pversion = product.split(":")[5]
        all_version_cpe = product.replace(pversion,"*")
        req = cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE KEYWORD = (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE CVE_CPE LIKE (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE KEYWORD = (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE CVE_CPE LIKE (?);", (product,"*"+product+"*",all_version_cpe,"*"+all_version_cpe+"*",))
    else:
        req = cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE KEYWORD = (?);", (product,)) 

    db_result_list = req.fetchall()
    cve_list = []
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:
            if result not in cve_list:
                cve_list.append(result)

    critical_cve, high_cve, medium_cve, low_cve, na_cve, exploitable_cve, expl_cve= [], [], [], [], [], [], []
    if "cpe" in product:
        req2 = cur.execute('SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True" AND KEYWORD = (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True" AND CVE_CPE LIKE (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True" AND KEYWORD = (?) UNION SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True" AND CVE_CPE LIKE (?);',(product,"*"+product+"*",all_version_cpe,"*"+all_version_cpe+"*",))
        db_result_list2 = req2.fetchall()
        for db_result_tuple2 in db_result_list2:
            for result2 in db_result_tuple2:
                if result2 not in expl_cve:
                    expl_cve.append(result2)
    else:
        req2 = cur.execute('SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True" AND KEYWORD = (?);',(product,))
        db_result_list2 = req2.fetchall()
        for db_result_tuple2 in db_result_list2:
            for result2 in db_result_tuple2:
                if result2 not in expl_cve:
                    expl_cve.append(result2)

    for cve in cve_list:
        db_result_list = cur.execute("SELECT CVE_ID,CVE_SCORE,STATUS FROM CVE_DATA WHERE CVE_ID = (?);", (cve,)).fetchall()
        for db_result_tuple in db_result_list:
            current_cve = []
            for result in db_result_tuple:
                current_cve.append(result)
            if current_cve[1] != None and current_cve[1] != "N/A" :
                current_cve[1] = current_cve[1].split(" ")[0]
                if 0 < float(current_cve[1]) <= 3.9:
                    low_cve.append(current_cve)
                elif 4.0 < float(current_cve[1]) <= 6.9:
                    medium_cve.append(current_cve)
                elif 7.0 < float(current_cve[1]) <= 8.9:
                    high_cve.append(current_cve)
                elif 9.0 < float(current_cve[1]) <= 10:
                    critical_cve.append(current_cve)
            elif current_cve[1] == "N/A":
                na_cve.append(current_cve)
            if cve in expl_cve:
                exploitable_cve.append(current_cve)

    return critical_cve, high_cve, medium_cve, low_cve, na_cve, exploitable_cve

def getParsedCpe(cpe):
    cpe = cpe.replace("*","- All versions")
    current_product = []
    disassmbled_cpe = cpe.split(":")
    pvendor = disassmbled_cpe[3].replace("_"," ").title()
    pproduct = disassmbled_cpe[4].replace("_"," ").title()
    subversion_infos = "("+disassmbled_cpe[6] +" "+ disassmbled_cpe[7] +" "+ disassmbled_cpe[8]+")"
    subversion_infos = subversion_infos.replace("- All versions","").replace(" - All versions","").replace("   )",")").replace("  )",")").replace(" )",")").replace("(   ","(").replace("(  ","(").replace("( ","(")
    if subversion_infos == "()" or subversion_infos == " " or subversion_infos == "( )":
        subversion_infos = ""
    try:    
        pversion = disassmbled_cpe[5].title()
    except Exception as e:
        handleException(e)
        pversion = ""
    if pversion == "-":
        product = pvendor+" "+pproduct
    else:
        product = pvendor+" "+pproduct+" "+pversion + subversion_infos

    return product
def getProductInfos(product):
	current_product = []
	if "cpe" in product:
		secmon_ptype = "CPE"
		fcpe = product
		cpe = product.replace("*","All")
		disassmbled_cpe = product.split(":")
		cpeptype = disassmbled_cpe[2]
		if cpeptype == "a":
			ptype = "Application"
		elif cpeptype == "o":
			ptype = "Operating System"
		elif cpeptype == "h":
			ptype = "Hardware"
		else: 
			ptype = "N/A" 
		pvendor = disassmbled_cpe[3].replace("_"," ").title()
		pproduct = disassmbled_cpe[4].replace("_"," ").title()
		try:
			pversion = disassmbled_cpe[5]
		except:
			pversion = ""
		if pversion == "-" or pversion == "":
			pversion = "All versions"
	else:
		secmon_ptype = "Keyword"
		fcpe = "N/A"
		pvendor = "N/A"
		pproduct = product
		ptype = "N/A"
		pversion = "All versions"
	current_product.append(secmon_ptype)
	current_product.append(fcpe)
	current_product.append(ptype)
	current_product.append(pvendor)
	current_product.append(pproduct)
	current_product.append(pversion)  
	return current_product
def getFormatedProductList():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT keyword FROM keyword_list")
    db_result_list = cur.fetchall()
    keywords = []
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:  
            keywords.append(result)
    cur.execute("SELECT cpe FROM cpe_list")
    db_result_list = cur.fetchall()
    cpes = []
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:  
            cpes.append(result)

    cpe_result = []
    for cpe in cpes:
        cpe = cpe.replace("*","All")
        current_product = []
        disassmbled_cpe = cpe.split(":")
        pvendor = disassmbled_cpe[3].replace("_"," ").title()
        pproduct = disassmbled_cpe[4].replace("_"," ").title()
        try:    
            pversion = disassmbled_cpe[5].title()
            if pversion == "All":
            	pversion = "- All versions"
            elif pversion == "-":
            	pversion = "- All versions"
        except Exception as e:
            handleException(e)
            pversion = ""
        product = pvendor+" "+pproduct+" "+pversion
        current_product.append(product)
        current_product.append(cpe.replace("All","*"))
        cpe_result.append(current_product)

    keyword_result = []
    for key in keywords:
        current_product = []
        current_product.append(key)
        current_product.append("N/A")
        keyword_result.append(current_product)
    return cpe_result+keyword_result
def showProducts(ptype_search):
    try:
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT keyword FROM keyword_list")
        db_result_list = cur.fetchall()
        keywords = []
        for db_result_tuple in db_result_list:
            for result in db_result_tuple:  
                keywords.append(result)
        cur.execute("SELECT cpe FROM cpe_list")
        db_result_list = cur.fetchall()
        cpes = []
        for db_result_tuple in db_result_list:
            for result in db_result_tuple:  
                cpes.append(result)

        cpe_result = []
        for cpe in cpes:
            cpe = cpe.replace("*","All")
            current_product = []
            disassmbled_cpe = cpe.split(":")
            ptype = ""
            if disassmbled_cpe[2] == "o":
                ptype = "Operating System"
            elif disassmbled_cpe[2] == "a":
                ptype = "Application"
            else:
                ptype = "Hardware"
            pvendor = disassmbled_cpe[3].replace("_"," ")
            pproduct = disassmbled_cpe[4].replace("_"," ")
            try:    
                pversion = disassmbled_cpe[5]
            except Exception as e:
                handleException(e)
                pversion = "All"
            current_product.append(ptype)
            current_product.append(pvendor)
            current_product.append(pproduct)
            current_product.append(pversion)
            current_product.append(cpe.replace("All","*"))
            cpe_result.append(current_product)

        keyword_result = []
        for key in keywords:
            current_product = []
            current_product.append("N/A")
            current_product.append("N/A")
            current_product.append(key)
            current_product.append("N/A")
            current_product.append("N/A")
            keyword_result.append(current_product)

        if ptype_search == "All":
            result = ["OK",keyword_result+cpe_result]
            return result
        elif "CPE" in ptype_search:
            result = ["OK",cpe_result]
            return result
        elif "keyword" in ptype_search:
            result = ["OK",keyword_result]
            return result
        else:
            result = ["NOK",""]
            return result
    except Exception as e:
        handleException(e)
        result = ["NOK",""]
        return result   
def mailTester(sender, passwd, smtpsrv, port, tls, receivers):
    try:
        if tls == "True":
            tls = "yes"
        else:
            tls = "no"
        script_path = os.path.abspath(__file__)
        dir_path = script_path.replace("secmon_lib.py","")
        language = ""
        con = sqlite3.connect(dir_path+'secmon.db')
        cur = con.cursor()
        cur.execute("SELECT language FROM config")
        db_result_tuple = cur.fetchone()
        for value in db_result_tuple:
            language = value
            body = ""
        with open(dir_path+'rss_template.html', 'r') as template:
            html_code = template.read()
            html_code = html_code.replace("<strong>Source : </strong> $SOURCE <br><br>","")
            html_code = html_code.replace("Notification","SECMON")
            html_code = html_code.replace("<strong>Title : </strong> $TITLE <br><br>","")
        if language =="en" or language == "EN":
            html_code = html_code.replace("RSS module","Test email")
            html_code = html_code.replace("<strong>Summary :</strong> $SUMMARY <br>","SECMON is an active security watch program that alerts you to the latest vulnerabilities and threats.")
            html_code = html_code.replace("Responsive HTML email templates","SECMON - Test email.")
            html_code = html_code.replace("See more details","Follow me on Github")
            body = html_code.replace("URL OF THE NEWS","https://github.com/Guezone")

        elif language =="fr" or language == "FR":
            html_code = html_code.replace("RSS module","Mail de test")
            html_code = html_code.replace("<strong>Summary :</strong> $SUMMARY <br>","SECMON est un programme de veille sécurité active\net vous averti des dernières vulnérabilités et menaces.")
            html_code = html_code.replace("Responsive HTML email templates","SECMON - Mail de test.")
            html_code = html_code.replace("See more details","Suivez-moi sur Github")
            html_code = html_code.replace("This email was sent by", "Cet email a été envoyé par")
            body = html_code.replace("URL OF THE NEWS","https://github.com/Guezone")   
        for receiver in receivers:
            smtpserver = smtplib.SMTP(smtpsrv,port)
            msg = MIMEMultipart()
            if language =="en" or language == "EN":
                msg['Subject'] = 'SECMON - Test email.'
            elif language =="fr" or language == "FR":
                msg['Subject'] = 'SECMON - Mail de test.'
                msg['From'] = sender
                msg['To'] = receiver
                msg.attach(MIMEText(body, 'html'))
            if tls == "yes":
                smtpserver.ehlo()
                smtpserver.starttls()
                smtpserver.login(sender, passwd)
                smtpserver.sendmail(sender, receiver, msg.as_string())
            elif tls == "no":
                smtpserver.login(sender, passwd)
                smtpserver.sendmail(sender, receiver, msg.as_string())
        receiver_conf = ';'.join(receivers)
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("UPDATE config SET sender = (?)", (sender,))
        cur.execute("UPDATE config SET password = (?)", ((str(base64.b64encode(passwd.encode("UTF-8"))).replace("b'","")).replace("'",""),))
        cur.execute("UPDATE config SET smtpsrv = (?)", (smtpsrv,))
        cur.execute("UPDATE config SET port = (?)", (port,))
        cur.execute("UPDATE config SET receiver = (?)", (receiver_conf,))
        cur.execute("UPDATE config SET tls = (?)", (tls,))
        con.commit()
        return True
    except Exception as e:
        handleException(e)
        return False

def get_db_connection():
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    conn = sqlite3.connect(dir_path+'secmon.db')
    conn.row_factory = sqlite3.Row
    return conn

def removeHTMLtags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
def changeCVEState(action, cve):
    
    db_change = ""
    if action == "ack":
        db_change = "Read"
    elif action == "trt":
        db_change = "Corrected"
    elif action == "false":
        db_change = "False positive"
    elif action == "utrt":
        db_change = "Unread"
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    conn = sqlite3.connect(dir_path+'secmon.db')
    cur = conn.cursor()
    # Check if CVE exist
    cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE CVE_ID = (?);", (cve.replace(" ",""),))
    db_result_list = cur.fetchall()
    db_result_str = ""
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:
            db_result_str+=result
    if cve not in db_result_str:
        raise
    else:
        cur.execute("UPDATE CVE_DATA SET STATUS = (?) WHERE CVE_ID = (?)", (db_change,cve.replace(" ","")))
        conn.commit()
        return db_change

def getRegisteredCveInfos(cve,full):
    cve_infos = {}
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    conn = get_db_connection()
    cur = conn.cursor()
    cve_av = "N/A"
    cve_ac = "N/A"
    cve_pr = "N/A"
    cve_ui = "N/A"
    cve_scope = "N/A"
    cve_confid = "N/A"
    cve_integrity = "N/A"
    cve_avail = "N/A"
    if full == True:
        nvd_base_url = "https://services.nvd.nist.gov/rest/json/cve/1.0/"   
        nvd_query = nvd_base_url+cve
        nvd_response = requests.get(url=nvd_query)
        try:
            nvd_data = nvd_response.json()
        except Exception as e:
            handleException(e)
            pass    
        try:
            cve_av = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['attackVector']
            cve_ac = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['attackComplexity']
            cve_pr = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['privilegesRequired']
            cve_ui = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['userInteraction']
            cve_scope = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['scope']
            cve_confid = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['confidentialityImpact']
            cve_integrity = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['integrityImpact']
            cve_avail = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['availabilityImpact']
        except Exception as e:
            pass
    req = cur.execute("SELECT CVE_ID, KEYWORD, STATUS,CVE_SCORE,CVE_DATE, CVE_DESCRIPTION, CVE_EVAL, CVE_CPE,CVE_SOURCES FROM CVE_DATA WHERE CVE_ID = (?);", (cve.replace(" ",""),))
    db_result = []
    for tup in req:
        for item in tup:
            db_result.append(item)
    try:
        cve_infos['cve_id'] = db_result[0]
        cve_infos['cve_description'] = db_result[5]
        cve_infos['cve_date'] = db_result[4]
        cve_infos['cve_score'] = db_result[3]
        cve_infos['cve_status'] = db_result[6]
        cve_infos['cve_cpe'] = db_result[7].split("\n")
        cve_infos['cve_sources'] = db_result[8].split("\n")
        cve_infos['cve_mgmt_status'] = db_result[2]
        cve_infos['cve_keymatch'] = db_result[1]
        cve_infos['cve_av'] = cve_av
        cve_infos['cve_ac'] = cve_ac
        cve_infos['cve_pr'] = cve_pr
        cve_infos['cve_ui'] = cve_ui
        cve_infos['cve_scope'] = cve_scope
        cve_infos['cve_confid'] = cve_confid
        cve_infos['cve_integrity'] = cve_integrity
        cve_infos['cve_avail'] = cve_avail
    except Exception as e:
        handleException(e)
        return None

    return cve_infos
def getUnregisteredCveInfos(cve):
    cve_infos = {}
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_lib.py","")
    conn = sqlite3.connect(dir_path+'secmon.db')
    cur = conn.cursor()
    cur.execute("SELECT CVE_ID FROM CVE_DATA WHERE CVE_ID = (?);", (cve.replace(" ",""),))
    cve_infos['cve_id'] = cve
    cve_id = cve
    db_result_list = cur.fetchall()
    db_result_str = ""
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:
            db_result_str+=result
    if cve not in db_result_str:
        cve_infos["cve_dbs"]="False"
    else:
        cve_infos["cve_dbs"]="True"

    nvd_base_url = "https://services.nvd.nist.gov/rest/json/cve/1.0/"
    nvd_query = nvd_base_url+cve_id
    nvd_response = requests.get(url=nvd_query)
    nvd_data = nvd_response.json()
    cve_av = "N/A"
    cve_ac = "N/A"
    cve_pr = "N/A"
    cve_ui = "N/A"
    cve_scope = "N/A"
    cve_confid = "N/A"
    cve_integrity = "N/A"
    cve_avail = "N/A"
    if 'result' in nvd_data.keys():
        cve_score = ""
        if not "impact" in nvd_data['result']['CVE_Items'][0].keys():
            cve_score = "N/A"
            try:    
                webpage = requests.get("https://nvd.nist.gov/vuln/detail/{}".format(cve_id))
                soup = BeautifulSoup(webpage.content, 'html.parser')
                cve_cna_score = soup.find(id='Cvss3CnaCalculatorAnchor')
                cve_cna_score = cve_cna_score.get_text()
                if cve_cna_score != "":
                    cve_score = cve_cna_score
                else:
                    cve_score = "N/A"
            except:
                    cve_score = "N/A"
        else:
            try:
                cve_score = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['baseScore']
                cve_av = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['attackVector']
                cve_ac = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['attackComplexity']
                cve_pr = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['privilegesRequired']
                cve_ui = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['userInteraction']
                cve_scope = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['scope']
                cve_confid = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['confidentialityImpact']
                cve_integrity = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['integrityImpact']
                cve_avail = nvd_data['result']['CVE_Items'][0]['impact']['baseMetricV3']['cvssV3']['availabilityImpact']
            except:
                cve_score = "N/A"
        weakness = ""
        try:
            weakness = nvd_data['result']['CVE_Items'][0]['cve']["problemtype"]["problemtype_data"][0]["description"][0]["value"]
        except:
            weakness = "N/A"
        published_date = nvd_data['result']['CVE_Items'][0]['publishedDate']
        cve_date = published_date.split("T")[0]
        fr_date = cve_date.split("-")
        cve_infos['cve_date'] = fr_date[2]+"/"+fr_date[1]+"/"+fr_date[0]
        cve_cpe = []
        if "configurations" in nvd_data['result']['CVE_Items'][0].keys():
            if nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
                for node in nvd_data['result']['CVE_Items'][0]['configurations']['nodes']:
                    if 'cpe_match' in node.keys():
                        for cpe_node in node['cpe_match']:
                            cve_cpe.append(cpe_node['cpe23Uri'])
        products = []
        if cve_cpe == []:
            products = ["N/A"]
        else:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("SELECT cpe FROM cpe_list")
            db_result_list = cur.fetchall()
            cpes = []
            for db_result_tuple in db_result_list:
                for result in db_result_tuple:  
                    cpes.append(result)
            for cpe in cve_cpe:
                cpe = cpe.replace("*","All")
                current_product = []
                disassmbled_cpe = cpe.split(":")
                ptype = ""
                if disassmbled_cpe[2] == "o":
                    ptype = "Operating System"
                elif disassmbled_cpe[2] == "a":
                    ptype = "Application"
                else:
                    ptype = "Hardware"
                pvendor = disassmbled_cpe[3].replace("_"," ")
                pproduct = disassmbled_cpe[4].replace("_"," ")
                try:    
                    pversion = disassmbled_cpe[5]
                except:
                    pversion = "All"
                current_product.append(ptype)
                current_product.append(pvendor)
                current_product.append(pproduct)
                current_product.append(pversion)
                current_product.append(cpe.replace("All","*"))
                match = ""
                if cpe.replace("All","*") in cpes:
                    match = "True - exact match"
                else:
                    for p in cpes:
                        partial_cpe = disassmbled_cpe[2]+":"+disassmbled_cpe[3]+":"+disassmbled_cpe[4]
                        if partial_cpe in p:
                            match = "True - partial match (require a manual check)"
                            break
                        else:
                            match = "False"
                current_product.append(match)
                products.append(current_product)




        cve_infos["cve_cpe"] = products
        published_date = nvd_data['result']['CVE_Items'][0]['publishedDate']
        formatted_date = published_date.split("T")[0]
        formatted_date = datetime.strptime(formatted_date,"%Y-%m-%d")
        date_2_days_ago = datetime.now() - timedelta(days=30)
        if (date_2_days_ago<=formatted_date) and (formatted_date<=datetime.now()):
            cve_date_status = "Recent"
        else:
            cve_date_status = "Old"
        if (cve_score=="N/A"):
            cve_status = cve_date_status+" - "+"Not yet rated (No score, no CPE)"
        else:
            cve_status = cve_date_status+" - "+"Valid evaluation"  
        cve_infos['cve_score'] = cve_score
        cve_infos['cve_av'] = cve_av
        cve_infos['cve_ac'] = cve_ac
        cve_infos['cve_pr'] = cve_pr
        cve_infos['cve_ui'] = cve_ui
        cve_infos['cve_scope'] = cve_scope
        cve_infos['cve_confid'] = cve_confid
        cve_infos['cve_integrity'] = cve_integrity
        cve_infos['cve_avail'] = cve_avail
        cve_infos['cve_status'] = cve_status  
        cve_infos['cve_weakness'] = weakness  
        exploits = []
        try:
            for e in CS.edbid_from_cve(cve):
                exploits.append(e)
        except:
            pass
        user,key = getGithubAPISettings()
        con = get_db_connection()
        cur = con.cursor()
        if user != "None" or key != "None":
            github_query = "https://api.github.com/search/repositories?q=exploit+"+cve
            github_response = requests.get(url=github_query,auth=(user,key))
            github_data = github_response.json()
            if "items" in github_data.keys():
                for i in github_data['items']:
                    exploits.append(i)
        if exploits == []:
            cve_infos['cve_expa'] = False
        else:
            cve_infos['cve_expa'] = True
        if 'reference_data' in nvd_data['result']['CVE_Items'][0]['cve']['references']:
            nvd_links = nvd_data['result']['CVE_Items'][0]['cve']['references']['reference_data']
            cve_sources = []
            for link in nvd_links:
                cve_sources.append(link['url'])
        else:
            cve_sources = []
        cve_infos['cve_sources'] = cve_sources
        cve_infos['cve_description'] = nvd_data['result']['CVE_Items'][0]['cve']['description']['description_data'][0]['value']
        
        req = cur.execute("SELECT STATUS FROM CVE_DATA WHERE CVE_ID = (?);", (cve,)).fetchone()
        if req == None:
            cve_infos['cve_mgmt_status'] = "Unavailable"
        else:
            cve_infos['cve_mgmt_status'] = ""
            for res in req:
                cve_infos['cve_mgmt_status'] += res
    else:
        raise ValueError('Failed to find CVE details on NVD API.')
    return cve_infos
def getCpeList():
    cur = get_db_connection().cursor()
    cur.execute("SELECT cpe FROM cpe_list")
    db_result_list = cur.fetchall()
    cpes = []
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:    
            cpes.append(result)
    return cpes
def getKeywordsList():    
    cur = get_db_connection().cursor()
    cur.execute("SELECT keyword FROM keyword_list")
    db_result_list = cur.fetchall()
    keywords = []
    for db_result_tuple in db_result_list:
        for result in db_result_tuple:    
            keywords.append(result)
    return keywords
def getRegisteredCveStats():
    conn = get_db_connection()
    db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
    low_counter = 0
    medium_counter = 0
    high_counter = 0
    critical_counter = 0
    for cve in db_result:
        current_cve = []
        
        for data in cve:
            current_cve.append(data)
        current_cve.pop(0)
        if current_cve[3] != "N/A" and current_cve[3] != None:
            current_cve[3] = current_cve[3].split(" ")[0]
            if 0 < float(current_cve[3]) <= 3.9:
                low_counter +=1
            elif 4.0 < float(current_cve[3]) <= 6.9:
                medium_counter +=1
            elif 7.0 < float(current_cve[3]) <= 8.9:
                high_counter +=1
            elif 9.0 < float(current_cve[3]) <= 10:
                critical_counter +=1
    stats = [low_counter,medium_counter,high_counter,critical_counter]
    return stats

def getRegisteredCveStatus():
    conn = get_db_connection()
    db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
    read_counter = 0
    unread_counter = 0
    corrected_counter = 0
    falsep_counter = 0
    total = 0
    for cve in db_result:
        current_cve = []
        total += 1
        for data in cve:
            current_cve.append(data)
        current_cve.pop(0)
        if current_cve[2] != "N/A" and current_cve[2] != None:
            if current_cve[2] == "Read":
                read_counter +=1
            elif current_cve[2] == "Unread" or current_cve[2] == "Native" or current_cve[2] == "Found when the product was added.":
                unread_counter +=1
            elif current_cve[2] == "Corrected":
                corrected_counter +=1
            elif current_cve[2] == "False positive": 
                falsep_counter +=1
    date = datetime.now()
    y = date.strftime("%Y")
    months = []
    months.append(date.strftime("%B"))
    months.append((date + relativedelta(months=-1)).strftime("%B"))
    months.append((date + relativedelta(months=-2)).strftime("%B"))
    months.append((date + relativedelta(months=-3)).strftime("%B"))
    months.append((date + relativedelta(months=-4)).strftime("%B"))
    months.append((date + relativedelta(months=-5)).strftime("%B"))
    digit_months = []
    digit_months.append(date.strftime("%m/%Y"))
    digit_months.append((date + relativedelta(months=-1)).strftime("%m/%Y"))
    digit_months.append((date + relativedelta(months=-2)).strftime("%m/%Y"))
    digit_months.append((date + relativedelta(months=-3)).strftime("%m/%Y"))
    digit_months.append((date + relativedelta(months=-4)).strftime("%m/%Y"))
    digit_months.append((date + relativedelta(months=-5)).strftime("%m/%Y"))
    months_data = [0,0,0,0,0,0]
    for cve in db_result:
        current_cve = []
        for data in cve:
            current_cve.append(data)
        current_cve.pop(0)
        if current_cve[4] != "N/A" and current_cve[4] != None:
            if digit_months[0] in current_cve[4]:
                months_data[0] +=1
            elif digit_months[1] in current_cve[4]:
                months_data[1] +=1
            elif digit_months[2] in current_cve[4]:
                months_data[2] +=1
            elif digit_months[3] in current_cve[4]:
                months_data[3] +=1
            elif digit_months[4] in current_cve[4]:
                months_data[4] +=1
            elif digit_months[5] in current_cve[4]:
                months_data[5] +=1
    stats = [read_counter,unread_counter,corrected_counter,falsep_counter,total,[ele for ele in reversed(months)],[ele for ele in reversed(months_data)]]
    return stats


def getRegisteredCve():
    conn = get_db_connection()
    db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
    cvelist = []
    for cve in db_result:
        current_cve = []
        for data in cve:
            current_cve.append(data)
        current_cve.pop(0)
        if "cpe" in current_cve[1]:
            current_cve[1] = getParsedCpe(current_cve[1])
        if current_cve[2] == "Unread" or "Native" in current_cve[2] or "Found" in current_cve[2]:
            current_cve.append("#e74a3b")
            current_cve.append("white")
        elif current_cve[2] == "Read":
            current_cve.append("#faaa3c")
            current_cve.append("black")
        elif current_cve[2] == "False positive":
            current_cve.append("#6c757d")
            current_cve.append("white")
        else:
            current_cve.append("#1cc88a")
            current_cve.append("white")
        try:
            float(current_cve[3])
        except:
            if current_cve[3] != "N/A":
                current_cve[3] = current_cve[3].split(" ")[0]

        if current_cve[3] != "N/A":
            current_cve[3] = current_cve[3].split(" ")[0]
            if 0 < float(current_cve[3]) <= 3.9:
                current_cve.append("#36b9cc")
                current_cve.append("white")
            elif 3.9 < float(current_cve[3]) <= 6.9:
                current_cve.append("#faaa3c")
                current_cve.append("black")
            elif 6.9 < float(current_cve[3]) <= 8.9:
                current_cve.append("#e74a3b")
                current_cve.append("white")
            elif 8.9 < float(current_cve[3]) <= 10:
                current_cve.append("#202020")
                current_cve.append("white")
        else:
            current_cve.append("#6c757d")
            current_cve.append("white")
        cvelist.append(current_cve)
    conn.close()
    return cvelist

def getUnexploitableCveIdList():
    conn = get_db_connection()
    db_result = conn.execute('SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "False"',).fetchall()
    cvelist = []
    for cve in db_result:
        for t in cve:
            cvelist.append(t)
    conn.close()
    return cvelist

def getExploitableCveIdList():
    conn = get_db_connection()
    db_result = conn.execute('SELECT CVE_ID FROM CVE_DATA WHERE EXPLOIT_FIND = "True"',).fetchall()
    cvelist = []
    for cve in db_result:
        for t in cve:
            cvelist.append(t)
    conn.close()
    return cvelist