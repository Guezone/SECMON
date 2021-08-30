# -*- coding: utf-8 -*-
""" 
SECMON - Source code of the SECMON python web backend.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
from flask import Flask, url_for, render_template, send_from_directory, request, flash, redirect, safe_join, session, url_for, session, abort
import jinja2.exceptions, sqlite3,requests, feedparser, re, os, random
from datetime import datetime, timedelta
from secmon_lib import getNewsTopSubject,getExploitableCveIdList,writeAuthLog,generateCveReport,getProductInfos,getParsedCpe,getRegisteredCveStatus, getTasks, getHighRiskProducts, getProductsStats, getCveByProduct,getRegisteredCve, getRegisteredCveStats,getFormatedProductList, getUnregisteredCveInfos, getRegisteredCveInfos, rss_feeds, get_db_connection, removeHTMLtags, changeCVEState,searchExploit, returnUsername, getSecretKey, messages, addProduct, deleteProduct,showProducts, mailTester
import secmon_monitor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from flask_simplelogin import SimpleLogin
from flask_simplelogin import login_required
from flask_simplelogin import is_logged_in
from multiprocessing import Process
import traceback, os.path
import urllib.parse
def secmon_auth(user):
    script_path = os.path.abspath(__file__)
    dir_path = script_path.replace("secmon_web.py","")
    con = sqlite3.connect(dir_path+'secmon.db')
    cur = con.cursor()
    db_hash = ""
    db_result = cur.execute("SELECT pass_hash FROM users WHERE username = (?);", (user['username'],))
    for data in db_result:
        for pwd in data:
            db_hash = pwd
    if check_password_hash(db_hash,user['password']):
        routes = []
        for e in app.url_map.iter_rules():
        	routes.append(str(e))
        if urllib.parse.unquote(request.url.split("=")[1]) not in routes:
        	writeAuthLog(f"secmon_web",user['username'],"failed",f"User {user['username']} has attempted to log in. Authentication failed: maflormed request.",request.remote_addr)
        	return False
        else:
        	writeAuthLog(f"secmon_web",user['username'],"success",f"User {user['username']} has attempted to log in. Authentication success.",request.remote_addr)
        	return True
    else:
        writeAuthLog(f"secmon_web",user['username'],"failed",f"User {user['username']} has attempted to log in. Authentication failed: bad username or password.",request.remote_addr)
        return False
app = Flask(__name__)
app.secret_key = getSecretKey()
app.jinja_env.globals.update(returnUsername=returnUsername)
SimpleLogin(app,login_checker=secmon_auth, messages=messages)
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)

@app.route('/login/<unauthorizedressource>')
@login_required
def redirectUnloggedUser(unauthorizedressource):
	return render_template('login.html')	

@app.route('/home')
@app.route('/')
@login_required
def home():
	mgmt_counters = getRegisteredCveStatus()
	total = mgmt_counters[4]
	counters = getRegisteredCveStats()
	plist = getFormatedProductList()
	product_number = getProductsStats()
	critical_products = getHighRiskProducts("hname")
	high_risk_product_number = 0
	for p in critical_products:
		high_risk_product_number+=1
	if total == 0:
		return render_template('home.html',low=counters[0],medium=counters[1],high=counters[2],critical=counters[3],products=critical_products, product_number=product_number,high_risk_product_number=high_risk_product_number,read=25,unread=25,corrected=25,falsep=25,months=mgmt_counters[5],months_data=mgmt_counters[6])
	else:

		return render_template('home.html',low=counters[0],medium=counters[1],high=counters[2],critical=counters[3],products=critical_products, product_number=product_number,high_risk_product_number=high_risk_product_number,read=int((mgmt_counters[0]/total)*100),unread=int((mgmt_counters[1]/total)*100),corrected=int((mgmt_counters[2]/total)*100),falsep=int((mgmt_counters[3]/total)*100),months=mgmt_counters[5],months_data=mgmt_counters[6])	
@app.route('/settings',methods=['GET', 'POST'])
@login_required
def settings():
	if request.method == 'POST':
		if request.form['btn'] == "Send":
			cur_password = request.form['cur_password']
			new_password = request.form['new_password']
			new_password2 = request.form['new_password2']
			if new_password == new_password2:
				script_path = os.path.abspath(__file__)
				dir_path = script_path.replace("secmon_web.py","")
				con = sqlite3.connect(dir_path+'secmon.db')
				cur = con.cursor()
				db_hash = ""
				current_user = returnUsername()
				db_result = cur.execute("SELECT pass_hash FROM users WHERE username = (?)", (current_user,))
				for data in db_result:
					for pwd in data:
						db_hash += pwd
				if check_password_hash(db_hash,cur_password):
					cur.execute("UPDATE users SET pass_hash = (?) WHERE username = (?)", (generate_password_hash(new_password,"sha512"),current_user))
					con.commit()
					flash("The password has been changed successfully.","success")
					return render_template('settings.html')
				else:
					flash("Bad current password.","danger")
					return render_template('settings.html')	
			else:
				flash("The passwords do not match.","danger")
				return render_template('settings.html')
		elif request.form['btn'] == "NewUser":
			username = request.form['username']
			password = request.form['password']
			password2 = request.form['password2']
			if password == password2:
				script_path = os.path.abspath(__file__)
				dir_path = script_path.replace("secmon_web.py","")
				con = sqlite3.connect(dir_path+'secmon.db')
				cur = con.cursor()
				result = []
				current_user = returnUsername()
				db_result = cur.execute("SELECT username FROM users")
				for data in db_result:
					for usr in data:
						result.append(usr)
				if username not in result:
					hashed_pwd = generate_password_hash(password, 'sha512')
					cur = con.cursor()
					cur.execute("INSERT INTO users (username, pass_hash) VALUES (?,?);", (username, hashed_pwd))
					con.commit()
					flash(f"User {username} successfully created.","success")
					return render_template('settings.html')
				else:
					flash(f"Failed to create {username} user because it already exist.","danger")
					return render_template('settings.html')	
			else:
				flash("The passwords do not match.","danger")
				return render_template('settings.html')			
		else:
			script_path = os.path.abspath(__file__)
			dir_path = script_path.replace("secmon_web.py","")
			con = sqlite3.connect(dir_path+'secmon.db')
			cur = con.cursor()
			current_user = returnUsername()
			db_result = cur.execute("DELETE FROM users WHERE username = (?)", (current_user,))
			con.commit()
			return redirect('logout')
	else:
		return render_template('settings.html')



@app.route('/vuln-mgmt',methods=['GET', 'POST'])
@login_required
def vuln_mgmt():
	if request.method == 'POST':
		try:
			cve = request.form['cve']
			action = request.form['btn']
			new_status = changeCVEState(action, cve)
			cvelist = getRegisteredCve()
			flash('{} management status was successfully updated to "{}.".'.format(cve,new_status), "success")
			return render_template('vuln-mgmt.html', cvelist=cvelist)
			
		except:
			cvelist = getRegisteredCve()
			flash('Error. Please enter a valid CVE value.', "danger")
			return render_template('vuln-mgmt.html', cvelist=cvelist)
			
	else:
		cvelist = getRegisteredCve()
		return render_template('vuln-mgmt.html', cvelist=cvelist)

@app.route('/rss-news')
@login_required
def rssNews():
	conn = get_db_connection()
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_web.py","")
	logfile = dir_path+"logs.txt"
	count = 0
	if os.path.isfile(logfile) == True:
		news = []
		for line in reversed(list(open(logfile, encoding='utf8'))):
			if "rss_poller" in line:
				log_rss_url = line.split('"')[11].replace('news_url="',"").replace('"',"")
				data = conn.execute("SELECT RSS_URL, title, rss_f, summary FROM RSS_DATA WHERE RSS_URL = (?);", (log_rss_url,)).fetchone()
				rss_data = []
				if data != None:
					for r_data in data:
						rss_data.append(r_data)
					rss_data[3] = str(removeHTMLtags(rss_data[3]))
					current_entry = [str(rss_data[0]),str(rss_data[1]),line.split('"')[5].replace('news_url="',"").replace('"',""),str(rss_data[3])]
					news.append(current_entry)
					count+=1
					if count >= 10:
						break
		if news == []:
			return render_template('rss-news.html',news=news,no_news="No news for the moment.")
		else:
			return render_template('rss-news.html',news=news)
@app.route('/cve-alerts')
@login_required
def cveAlerts():
	conn = get_db_connection()
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_web.py","")
	logfile = dir_path+"logs.txt"
	count = 0
	cves = []
	if os.path.isfile(logfile) == True:
		
		for line in reversed(list(open(logfile, encoding='utf8'))):
			if """source_script="cve_poller" """ in line and """type="new" """ in line:
				it = []
				cve_id = re.findall('CVE-\d{4}-\d{4,7}',line)[0]
				infos = getRegisteredCveInfos(cve_id, full=False)
				if infos != None:
					it.append(infos['cve_id'])
					it.append(infos['cve_description'])
					it.append(infos['cve_date'])
					it.append(infos['cve_score'])
					it.append(infos['cve_status'])
					it.append(infos['cve_cpe'])
					it.append(infos['cve_sources'])
					it.append(infos['cve_mgmt_status'])
				else:
					it.append(cve_id)
					it.append("This CVE is no longer in the database. This may be due to a deletion of the product that concerns it.")
				cves.append(it)
				count+=1
				if count >= 10:
					break
		if cves == []:
			return render_template('cve-alerts.html',cves=cves, no_alerts="No alert for the moment.")
		else:
			return render_template('cve-alerts.html',cves=cves)
@app.route('/cyber-threats')
@login_required
def topCyberSubject():
	words = getNewsTopSubject()
	return render_template('cyber-threats.html',words=words)
@app.route('/cve-updates')
@login_required
def cveUpdates():
	conn = get_db_connection()
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_web.py","")
	logfile = dir_path+"logs.txt"
	count = 0
	cves = []
	if os.path.isfile(logfile) == True:
		for line in reversed(list(open(logfile, encoding='utf8'))):
			if "cve_updater" in line and 'type="update"' in line:
				it = []
				cve_id = re.findall('CVE-\d{4}-\d{4,7}',line)[0]
				it.append(cve_id)
				it.append(line.split('"')[23].replace('message="',"").replace('"'," "))
				cves.append(it)
				count+=1
				if count >= 20:
					break
		if cves == []:
			return render_template('cve-updates.html',cves=cves, no_updates="No CVE updates found recently.")
		else:
			return render_template('cve-updates.html',cves=cves)

@app.route('/search',methods=['GET', 'POST'])
@login_required
def search():
	cve = ""
	if request.method == 'POST':
		if request.form['cve'] != "" and request.form['cve'] != " ":
			try:	
				cve = request.form['cve'].upper()
				infos = getUnregisteredCveInfos(cve)
				if infos['cve_weakness'] != "N/A":
					weakness_nb = infos['cve_weakness'].split("-")[1]
				return render_template('result.html',back_path="search",cve_id=infos['cve_id'] ,cve_summary=infos['cve_description'],cve_dbs=infos['cve_dbs'],cve_date=infos['cve_date'],cve_score=infos['cve_score'],cve_status=infos['cve_status'],cve_cpe=infos['cve_cpe'],cve_sources=infos['cve_sources'],cve_av=infos['cve_av'],cve_ac=infos['cve_ac'],cve_pr=infos['cve_pr'],cve_ui=infos['cve_ui'],cve_scope=infos['cve_scope'],cve_confid=infos['cve_confid'],cve_integrity=infos['cve_integrity'],cve_avail=infos['cve_avail'],cve_expa=infos['cve_expa'],cve_weakness=infos['cve_weakness'],weakness_nb=weakness_nb,back="../")
			except Exception as e:
				cve = request.form['cve'].upper()
				flash("""This CVE does not exist or the data is not available on the API. Please check manually on """, "danger")
				nvd_link = "https://nvd.nist.gov/vuln/detail/"+cve
				return render_template('search.html', nvd_link=nvd_link)
		else:
			flash("""Please enter a value.""", "warning")
			return render_template('search.html')
	else:
		return render_template('search.html')

@app.route('/exploits',methods=['GET', 'POST'])
@login_required
def exploits():
	cve = ""
	exploitables_cve = getExploitableCveIdList()
	if request.method == 'POST':
		if 'psearchbtn' in request.form:
			if request.form['cve'] != "" and request.form['cve'] != " ":
				cve = request.form['cve'].upper()
				if "CVE" not in cve:
					flash("""Please enter a valid CVE ID.""", "warning")
					return render_template('exploits.html',cvelist=exploitables_cve)					
				infos = searchExploit(cve, False)
				if infos == []:
					flash("""Unable to find exploits for this CVE value.""", "warning")
					return render_template('exploits.html',cvelist=exploitables_cve)
				else:
					return render_template('exploits.html',result=infos,cvelist=exploitables_cve)
			else:
				flash("""Please enter a value.""", "warning")
				return render_template('exploits.html',cvelist=exploitables_cve)
		else:
			return render_template('exploits.html',cvelist=exploitables_cve)

	else:
		return render_template('exploits.html',cvelist=exploitables_cve)

@app.route('/cve-exploits/<cve_id>')
@login_required
def cveExploits(cve_id):
	exploitables_cve = getExploitableCveIdList()				
	infos = searchExploit(cve_id, False)
	return render_template('exploits.html',result=infos,cvelist=exploitables_cve,back="../../")

@app.route('/details-cve-low')
@login_required
def getLowCVE():
	conn = get_db_connection()
	db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
	low_cve_id = []
	cve_list_LOW = []
	count = 0
	for result in db_result:
		current_cve = []
		for data in result:
			current_cve.append(data)
		current_cve.pop(0)
		if current_cve[3] != "N/A":
			current_cve[3] = current_cve[3].split(" ")[0]
			if 0 <= float(current_cve[3]) <= 3.9:
				low_cve_id.append(current_cve[0])
				count +=1

	for cve in low_cve_id:
		infos = getRegisteredCveInfos(cve,full=False)
		it = []
		it.append(infos['cve_id'])
		it.append(infos['cve_description'])
		it.append(infos['cve_date'])
		it.append(infos['cve_score'])
		it.append(infos['cve_status'])
		it.append(infos['cve_cpe'])
		it.append(infos['cve_sources'])
		it.append(infos['cve_mgmt_status'])
		cve_list_LOW.append(it)
	if count == 0:
		result = False
		return render_template('details-cve-low.html',result=result)
	else:	
		return render_template('details-cve-low.html',cve_list_LOW=cve_list_LOW)


@app.route('/details-cve-medium')
@login_required
def getMediumCVE():
	conn = get_db_connection()
	db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
	medium_cve_id = []
	cve_list_MEDIUM = []
	count = 0
	for result in db_result:
		current_cve = []
		for data in result:
			current_cve.append(data)
		current_cve.pop(0)
		if current_cve[3] != "N/A":
			current_cve[3] = current_cve[3].split(" ")[0]
			if 4.0 <= float(current_cve[3]) <= 6.9:
				medium_cve_id.append(current_cve[0])
				count +=1

	for cve in medium_cve_id:
		infos = getRegisteredCveInfos(cve,full=False)
		it = []
		it.append(infos['cve_id'])
		it.append(infos['cve_description'])
		it.append(infos['cve_date'])
		it.append(infos['cve_score'])
		it.append(infos['cve_status'])
		it.append(infos['cve_cpe'])
		it.append(infos['cve_sources'])
		it.append(infos['cve_mgmt_status'])
		cve_list_MEDIUM.append(it)
	if count == 0:
		result = False
		return render_template('details-cve-medium.html',result=result)
	else:	
		return render_template('details-cve-medium.html',cve_list_MEDIUM=cve_list_MEDIUM)

@app.route('/details-cve-high')
@login_required
def getHighCVE():
	conn = get_db_connection()
	db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
	high_cve_id = []
	cve_list_HIGH = []
	count = 0
	for result in db_result:
		current_cve = []
		for data in result:
			current_cve.append(data)
		current_cve.pop(0)
		if current_cve[3] != "N/A":
			current_cve[3] = current_cve[3].split(" ")[0]
			if 7.0 <= float(current_cve[3]) <= 8.9:
				high_cve_id.append(current_cve[0])
				count +=1

	for cve in high_cve_id:
		infos = getRegisteredCveInfos(cve,full=False)
		it = []
		it.append(infos['cve_id'])
		it.append(infos['cve_description'])
		it.append(infos['cve_date'])
		it.append(infos['cve_score'])
		it.append(infos['cve_status'])
		it.append(infos['cve_cpe'])
		it.append(infos['cve_sources'])
		it.append(infos['cve_mgmt_status'])
		cve_list_HIGH.append(it)
	if count == 0:
		result = False
		return render_template('details-cve-high.html',result=result)
	else:	
		return render_template('details-cve-high.html',cve_list_HIGH=cve_list_HIGH)

@app.route('/details-cve-critical')
@login_required
def getCriticalCVE():
	conn = get_db_connection()
	db_result = conn.execute('SELECT * FROM CVE_DATA',).fetchall()
	critical_cve_id = []
	cve_list_CRITICAL = []
	count = 0
	for result in db_result:
		current_cve = []
		for data in result:
			current_cve.append(data)
		current_cve.pop(0)
		if current_cve[3] != "N/A":
			current_cve[3] = current_cve[3].split(" ")[0]
			if 9.0 <= float(current_cve[3]) <= 10:
				critical_cve_id.append(current_cve[0])
				count +=1

	for cve in critical_cve_id:
		infos = getRegisteredCveInfos(cve,full=False)
		it = []
		it.append(infos['cve_id'])
		it.append(infos['cve_description'])
		it.append(infos['cve_date'])
		it.append(infos['cve_score'])
		it.append(infos['cve_status'])
		it.append(infos['cve_cpe'])
		it.append(infos['cve_sources'])
		it.append(infos['cve_mgmt_status'])
		cve_list_CRITICAL.append(it)
	if count == 0:
		result = False
		return render_template('details-cve-critical.html',result=result)
	else:	
		return render_template('details-cve-critical.html',cve_list_CRITICAL=cve_list_CRITICAL)
@app.route('/config',methods=['GET', 'POST'])
@login_required
def config():
	if request.method == 'POST':
		if "submit_smtp_config" in request.form:
			regex = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
			sender = request.form['email']
			if not (re.search(regex,sender)):
				flash("Wrong email format for the sender.","danger")
				return render_template('config.html')
			smtp_login = request.form['login']

			smtp_password = request.form['pass1']
			password2 = request.form['pass2']
			smtpsrv = request.form['server']
			port = request.form['port']
			receivers = request.form['recipients']
			if password != password2:
				flash("The two passwords do not match. ","danger")
				return render_template('config.html')
			try:
				int(port)
			except:
				flash("Invalid port format. ","danger")
				return render_template('config.html')				

			if ";" in receivers:
				receivers = receivers.split(";")
			else:
				mono_rec = receivers
				receivers = []
				receivers.append(mono_rec)
			for r in receivers:
				if not (re.search(regex,r)):
					flash("Wrong email format for the recipients. ","danger")
					return render_template('config.html')
			tls = request.form['tls']
			if mailTester(smtp_login, smtp_password, smtpsrv, port, tls, sender, receivers):
				flash("The test email was sent successfully. ","success")
				return render_template('config.html')				
			else:
				flash("Failed to send test email. ","danger")
				return render_template('config.html')
	else:	
		return render_template('config.html')

@app.route('/reports',methods=['GET', 'POST'])
@login_required
def reports():
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_web.py","")
	filename = "SECMON-CVE-Report.xlsx"
	if request.method == 'POST':
		if not 'btn-full' in request.form:
			start_date = request.form["start_date"].split('-')
			end_date = request.form["end_date"].split('-')
			start_date = start_date[2]+"/"+start_date[1]+"/"+start_date[0]
			end_date = end_date[2]+"/"+end_date[1]+"/"+end_date[0]
			start_date_obj = datetime.strptime(start_date, "%d/%m/%Y")
			end_date_obj = datetime.strptime(end_date, "%d/%m/%Y")
			now = datetime.now()
			if start_date_obj >= end_date_obj:
				flash("Invalid date range. ","danger")
				return render_template('reports.html')
			elif end_date_obj > now:
				flash("Invalid end date. ","danger")
				return render_template('reports.html')			
			else:
				generateCveReport(start_date_obj,end_date_obj,isFull=False)
				return send_from_directory(directory=dir_path, filename=filename,as_attachment=True)
		else:
			generateCveReport(datetime.strptime("01/01/2020", "%d/%m/%Y"),datetime.strptime("01/01/2020", "%d/%m/%Y"),isFull=True)
			return send_from_directory(directory=dir_path, filename=filename,as_attachment=True)
	else:
		if os.path.isfile(dir_path+filename):
			os.remove(dir_path+filename)
		return render_template('reports.html')

@app.route('/logs')
@login_required
def logs():
	script_path = os.path.abspath(__file__)
	dir_path = script_path.replace("secmon_web.py","")
	logfile = dir_path+"logs.txt"
	logs_lines = []
	count = 0
	if os.path.isfile(logfile) == True:
		try:
			for line in reversed(list(open(logfile, encoding='utf8'))):
				logs_lines.append(line.rstrip())
				count+=1
				if count >= 100:
					break
		except:
			flash("""Error. You haven't permissions for read the log file.""", "danger")
			return render_template('logs.html')
	else:
		flash("""Error. The log file is not present.""", "danger")
		return render_template('logs.html')
	return render_template('logs.html', logs=logs_lines)

@app.route('/cve/<cve_id>')
@login_required
def cveInfos(cve_id):
	infos = getUnregisteredCveInfos(cve_id)
	if infos['cve_weakness'] != "N/A":
		weakness_nb = infos['cve_weakness'].split("-")[1]
	else:
		weakness_nb = "N/A"
	return render_template('result.html',back_path="../../vuln-mgmt",cve_id=infos['cve_id'] ,cve_summary=infos['cve_description'],cve_dbs=infos['cve_dbs'],cve_date=infos['cve_date'],cve_score=infos['cve_score'],cve_status=infos['cve_status'],cve_cpe=infos['cve_cpe'],cve_sources=infos['cve_sources'],cve_av=infos['cve_av'],cve_ac=infos['cve_ac'],cve_pr=infos['cve_pr'],cve_ui=infos['cve_ui'],cve_scope=infos['cve_scope'],cve_confid=infos['cve_confid'],cve_integrity=infos['cve_integrity'],cve_avail=infos['cve_avail'],cve_expa=infos['cve_expa'],cve_weakness=infos['cve_weakness'],weakness_nb=weakness_nb,back="../../")


@app.route('/by-product-vulns',methods=['GET', 'POST'])
@login_required
def byProductVulns():
	if request.method == 'POST':
		product = request.form['product_selection']
		critical_cve, high_cve, medium_cve, low_cve, na_cve, exploitable_cve = getCveByProduct(product,True)
		total_count = len(critical_cve)+len(high_cve)+len(medium_cve)+len(low_cve)+len(na_cve)
		counters = [total_count,len(critical_cve),len(high_cve),len(medium_cve),len(low_cve),len(na_cve),len(exploitable_cve)]
		pinfos = getProductInfos(product)
		if "cpe" in product:
			product = getParsedCpe(product)
		else:
			product = pinfos[4]
		return render_template('product-card.html', critical_cve=critical_cve, high_cve=high_cve, medium_cve=medium_cve, low_cve=low_cve, na_cve=na_cve, exploitable_cve=exploitable_cve,product=product,pinfos=pinfos,counters=counters)
	else:
		plist = getFormatedProductList()
		critical_p = getHighRiskProducts("all")
		critical_cpe = []
		critical_keyword = []
		for p in critical_p:
			if p[0] == "N/A":
				critical_keyword.append(p)
			else:
				critical_cpe.append(p)
		return render_template('by-product-vulns.html', plist=plist,crit_cpe=critical_cpe,crit_key=critical_keyword)
@app.route('/about')
@login_required
def about():
	return render_template('about.html')
@app.route('/tasks')
@login_required
def tasks():
	tasks = getTasks()
	return render_template('tasks.html',tasks=tasks)
@app.route('/product-mgmt',methods=['GET', 'POST'])
@login_required
def psearch():
	if request.method == 'POST':
		if 'psearchbtn' in request.form:
			if request.form['product'] != "" and request.form['product'] != " ":
				product_user_search = request.form['product']
				nvd_query = "https://services.nvd.nist.gov/rest/json/cpes/1.0?keyword="+product_user_search+"&resultsPerPage=1000"
				nvd_response = requests.get(url=nvd_query)
				try:	
					nvd_data = nvd_response.json()
				except:
					flash("""No results.""", "warning")
					return render_template('product-mgmt.html')					
				if 'result' in nvd_data.keys():
					cpelist = nvd_data['result']['cpes']
					result = []
					if cpelist != []:
						for product in cpelist:
							current_product = []
							product = product['cpe23Uri'].replace("*","All")
							disassmbled_cpe = product.split(":")
							ptype = ""
							if disassmbled_cpe[2] == "o":
								ptype = "Operating System"
							elif disassmbled_cpe[2] == "a":
								ptype = "Application"
							else:
								ptype = "Hardware"

							pvendor = disassmbled_cpe[3].replace("_"," ")
							pproduct = disassmbled_cpe[4].replace("_"," ")
							pversion = disassmbled_cpe[5]
							pcpe = product.replace("All","*")
							current_product.append(ptype)
							current_product.append(pvendor)
							current_product.append(pproduct)
							current_product.append(pversion)
							current_product.append(pcpe)
							result.append(current_product)
						return render_template('product-mgmt.html', result=result)	
					else:
						flash("""No results.""", "warning")
						return render_template('product-mgmt.html')	
				else:
					flash("""No results.""", "warning")
					return render_template('product-mgmt.html')				


		elif 'submit_product_action' in request.form:
			action = request.form['product_action']
			ptype = request.form['product_type']
			key_or_cpe = request.form['keyword']
			if action == "Add":
				p = Process(target=addProduct, args=(ptype,key_or_cpe,))
				p.start()
				flash('New product registration in progress... You can track new tasks <a href="/tasks">Tasks</a> tab. ',"success")
				return render_template('product-mgmt.html')			
			else:
				if deleteProduct(ptype, key_or_cpe) == "OK":
					flash("The product has been deleted successfully. ","success")
					return render_template('product-mgmt.html')
				else:
					flash("Unable to delete this product. ","danger")
					return render_template('product-mgmt.html')	
		elif "submit_import_csv_file" in request.form:
			script_path = os.path.abspath(__file__)
			dir_path = script_path.replace("secmon_web.py","")
			file = request.files.get("file")
			filename = file.filename
			if filename.split(".")[1] == "csv" and len(filename.split(".")) == 2:
				try:
					file.save(os.path.join(dir_path,filename))
					f = open(dir_path+filename,"r").readlines()
					for line in f:
						line = line.replace("\\\n","").replace("\n","")
						if line != "" and line != "\n":
							if "cpe" in line:
								p = Process(target=addProduct, args=("CPE",line,))
								p.start()
							else:
								p = Process(target=addProduct, args=("keyword",line,))
								p.start()
					flash('File successfully uploaded. You can track new tasks in the "Administration > Task." tab. ', "success")
					os.remove(dir_path+filename)
					return render_template('product-mgmt.html')
				except:
					flash('Bad format. Unable to read your csv file. ', "success")
					os.remove(dir_path+filename)
					return render_template('product-mgmt.html')
			else:
				flash('Bad format. Unable to read the file. ', "danger")
				return render_template('product-mgmt.html')
			
		elif "submit_product_display" in request.form:
			ptype = request.form["product_type"]
			if showProducts(ptype)[0] == "OK":
				plist = showProducts(ptype)[1]
				return render_template('product-mgmt.html', plist=plist)
			else:
				flash("Unable to display your product list. ","danger")
				return render_template('product-mgmt.html')

		else:
			flash("""Please enter a value.""", "warning")
			return render_template('product-mgmt.html')

	else:
		return render_template('product-mgmt.html')
@app.route('/<path:resource>')
def serveStaticResource(resource):
	return send_from_directory('static/', resource)
	
@app.errorhandler(Exception)
def handle_exception(error):
	now = datetime.now()
	now = now.strftime("%d/%m/%Y, %H:%M:%S")
	print(f"################## NEW GUI ERROR AT {now} ##################")
	print(f"######## URL : {request.base_url} ##########")
	print(traceback.print_exc())
	print("################## PLEASE REPORT THIS ON GITHUB ##################")
	return render_template("errors.html"), 200
if __name__ == '__main__':
    app.run(debug=False,threaded=True)
    




