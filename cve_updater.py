# -*- coding: utf-8 -*-
""" 
SECMON - Source code of the SECMON updater script.
"""
__author__ = "Aubin Custodio"
__copyright__ = "Copyright 2021, SECMON"
__credits__ = ["Aubin Custodio","Guezone"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "2.1"
__maintainer__ = "Aubin Custodio"
__email__ = "custodio.aubin@outlook.com"
from secmon_lib import writeNewExploitFoundLog, getUnexploitableCveIdList,getGithubAPISettings,getRegisteredCveInfos, get_db_connection, getUnregisteredCveInfos, getFormatedProductList, getCveByProduct, writeNewHighRiskProductLog, writeCveTypeLog
from datetime import datetime
import os,requests
import cve_searchsploit as CS
script_path = os.path.abspath(__file__)
dir_path = script_path.replace("cve_updater.py","")
log_file = dir_path+"logs.txt"
print("------------ CVE Module - Update ------------")
timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
print("Starting at : "+timestamp)
print("---------------------------------------------")
CS.update_db()
con = get_db_connection()
cur = con.cursor()
cve_list = getUnexploitableCveIdList()
for cve in cve_list:
	exploitdb_exploits = CS.edbid_from_cve(cve)
	if len(exploitdb_exploits) > 0:
		cur.execute("UPDATE CVE_DATA SET EXPLOIT_FIND = (?) WHERE CVE_ID = (?)", ("True",cve))
		con.commit()
		print("Exploit found for "+cve+" from Exploit-DB")
		writeNewExploitFoundLog("cve_updater","exploit-db",cve,f"New(s) exploit found for {cve} from Exploit-DB !")
print("\nSearch Github Exploit for registered CVE...")
cve_list = getUnexploitableCveIdList()
user,key = getGithubAPISettings()
con = get_db_connection()
cur = con.cursor()
if user == "None" or key == "None":
	print("No Github API configuration found.")
else:
	for cve in cve_list:
		github_query = "https://api.github.com/search/repositories?q=exploit+"+cve
		github_response = requests.get(url=github_query,auth=(user,key))
		github_data = github_response.json()
		if "items" in github_data.keys():
			if len(github_data['items']) > 0:
				cur.execute("UPDATE CVE_DATA SET EXPLOIT_FIND = (?) WHERE CVE_ID = (?)", ("True",cve))
				con.commit()
				print("Exploit found for "+cve+" from Github")
				writeNewExploitFoundLog("cve_updater","github",cve,f"New exploit found for {cve} from Github !")
print("\nUpdating high risk product list....")
plist = getFormatedProductList()
con = get_db_connection()
cur = con.cursor()
critical_product = []
old_critical_product = []
cur.execute("SELECT hname FROM high_risk_products;")
db_result_list = cur.fetchall()
for db_result_tuple in db_result_list:
	for result in db_result_tuple:
		if result not in old_critical_product:
			old_critical_product.append(result)
for product in plist:
	if "cpe" in product[1]:
		target_product = product[1]
	else:
		target_product = product[0]
	critical_cve, high_cve, medium_cve, low_cve, na_cve, exploitable_cve = getCveByProduct(target_product, True)
	if exploitable_cve != []:
		if product[0] not in old_critical_product:
			critical_product.append(product)
			print("New critical product : "+product[0])
			cur.execute("INSERT INTO high_risk_products (cpe,hname) VALUES (?,?);", (product[1],product[0]))
			writeNewHighRiskProductLog("cve_updater",product[1],f"A new critical product was discovered. ({product[1]})")
			con.commit()
print("\nUpdating affected products and CVSS score related to your CVE list...")
con = get_db_connection()
cur = con.cursor()
req = cur.execute("SELECT CVE_ID FROM CVE_DATA")
indb_cve_list = []
changelog = []
for tup in req:
	for cve in tup:
		indb_cve_list.append(cve)
for cve in indb_cve_list:
	try:
		try:
			before_update = getRegisteredCveInfos(cve, full=True)
			after_update = getUnregisteredCveInfos(cve)
		except:
			continue
		for cpe in before_update['cve_cpe']:
			if cpe == '':
				before_update['cve_cpe'].remove(cpe)
		for item in before_update.keys():
			if item == "cve_score":
				if str(after_update[item]) != str(before_update[item]):
					writeCveTypeLog("cve_updater",cve,"update","N/A",str(after_update[item]),"N/A","N/A","N/A","N/A","The CVSS Score was changed from {} to {}.".format(str(before_update[item]), str(after_update[item])))
					changelog.append(cve+" - There has been a change in the CVSS score : {} TO {}\n".format(str(before_update[item]), str(after_update[item])))
					print(cve+" - There has been a change in the CVSS score : {} TO {}\n".format(str(before_update[item]), str(after_update[item])))
					cur.execute("UPDATE CVE_DATA SET CVE_SCORE = (?) WHERE CVE_ID = (?)", (str(after_update[item]),cve))
					con.commit()
			elif item == "cve_cpe":
				if after_update[item] != before_update[item]:
					change = ""
					diff = list(set(after_update[item])-set(before_update[item]))
					if diff == []:
						change = "removed"
						diff = list(set(before_update[item])-set(after_update[item]))
						cpe_diff = ""
						for elem in diff:
							if len(diff) == 1 or elem == diff[-1]:
								cpe_diff += elem
							else:
								cpe_diff = cpe_diff+elem+" AND "
					else:
						change = "added"
						cpe_diff = ""
						for elem in diff:
							if len(diff) == 1 or elem == diff[-1]:
								cpe_diff += elem
							else:
								cpe_diff = cpe_diff+elem+" AND "
					writeCveTypeLog("cve_updater",cve,"update","N/A",str(after_update[item]),"N/A","N/A","N/A","N/A","The following products have been {} : {} \n".format(change,cpe_diff))
					changelog.append(cve+" - The following products have been {} : {} \n".format(change,cpe_diff))
					print(cve+" - The following products have been {} : {} \n".format(change,cpe_diff))
					new_cpe = ""
					for cpe in after_update[item]:
						new_cpe+=(cpe+"\n")
					cur.execute("UPDATE CVE_DATA SET CVE_CPE = (?) WHERE CVE_ID = (?)", (new_cpe,cve))
					con.commit()
	except:
		continue
if changelog == []:
	print("No CVE have been updated. \n")
	
timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
print("---------------------------------------------")
print("Finished at : "+timestamp)
print("---------------------------------------------")