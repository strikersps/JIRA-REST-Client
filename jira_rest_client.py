from jira import JIRA,JIRAError
import json
import pymysql.cursors
import pandas as pd
import os,sys
import argparse

try:
	parser = argparse.ArgumentParser()
	parser.add_argument('-u',type=str,default="",help="username of user",required=True)
	parser.add_argument('-p',type=str,default="",help="user password",required=True)
	parser.add_argument('-hname',type=str,default="",help="hostname",required=True)
	parser.add_argument('-dbname',type=str,default="",help="database name")
	args = parser.parse_args()
except:
	print("You have not passed the arguments!")
	sys.exit(1)

def initialiseProgram():
	try:
		# print("%s %s %s %s" %(args.hname,args.u,args.p,args.dbname))
		conn = pymysql.connect(args.hname,args.u,args.p,args.dbname)
		cur = conn.cursor()
		# query = "select searchKey,value from "+args.dbname+".tblConfigure where (searchKey = 'SETUP/JIRACONN/AUTH_TYPE/BASIC' or searchKey = 'ISSUE/PROJECT/PROJECT_NAME' or searchKey = 'ISSUE/ASSIGNEE/ASSIGNEE_NAME') and isActive=1"
		query = "select searchKey,value from "+args.dbname+".tblConfigure where idConfigure >75 && isActive=1"
		cur.execute(query)
		result = cur.fetchall()
		result_dict = dict((x,y) for x,y in result)
		# print(result_dict)
	except pymysql.Error as e:
		print(e)
		sys.exit(1) # Program will get terminated
	return result_dict

# Using basic authentication for using the resources/information of the resource owner.
# username and password is sent using base64 encoding.
# you can use OAuth 1.0a Authentication protocol but for that you need to register this app
# as a web app
def basicAuthentication(username,password,server):
	try:
		jira = JIRA(basic_auth=(username,password),options={"server":server})
		print("JIRA Authentication Sucessfull")
		return (True,jira)
	except JIRAError as e:
		error = jiraErrorinfo(e.status_code)
		return (False,error)

def jiraErrorinfo(statusCode):
	if statusCode == 401:
		return ("The Authentication Details You Provided is Invalid")
	elif statusCode == 200:
		return ("It Worked")
	elif statusCode == 201:
		return ("The resource was created successfully. The body should contain a “links” map with a “self” field that contains the new URL to access the created resource. Alternatively, the URL will be in the “Location” header")
	elif statusCode == 202:
		return ("When using test_auth=true, this response code indicates that the auth_token is valid.")
	elif statusCode == 204:
		return ("The request succeeded and the response does not contain any content.")
	elif statusCode == 400:
		return ("The request was invalid. You may be missing a required argument or provided bad data. An error message will be returned explaining what happened.")
	elif statusCode == 403:
		return ("You don’t have permission to complete the operation or access the resource.")
	elif statusCode == 404:
		return ("You requested an invalid method")
	elif statusCode == 405:
		return ("The method specified in the Request-Line is not allowed for the resource identified by the Request-URI. (used POST instead of PUT)")
	elif statusCode == 429:
		return ("Too Many Requests: You have exceeded the rate limit")
	elif statusCode == 500:
		return ("Something is wrong on our end. We’ll investigate what happened. Feel free to contact us.")
	elif statusCode == 503:
		return ("The method you requested is currently unavailable (due to maintenance or high load).")

def projectDetails(jira):
	proList = jira.projects()
	print("Total Number of Projects In An Account: %s" %len(proList))
	return proList
'''
def printProjectDetails(jira, list):
	t = PrettyTable(['ID','Key','Name','Type','Description','Lead','Active'])
	for i in list:
		info = jira.project(i)
		if info.description is not "":
			t.add_row([i.id,i.key,i.name,i.projectTypeKey,info.description,info.lead.displayName,info.lead.active])
		else:
			t.add_row([i.id,i.key,i.name,i.projectTypeKey,'No Description',info.lead.displayName,info.lead.active])
	print(t)
'''

def binarySearch(key,list):
	start = 0
	end = len(list)-1
	while (start <= end):
		mid = int(((end-start)/2) + start)
		if key in list[mid].name:
			return mid
		elif list[mid].name > key:
			end = mid-1
		else:
			start = mid+1
	return (-1)

def queryExecution(conn,idWebRtc):
	if idWebRtc == False:
		query = "select * from "+args.dbname+".tblSessWebRtc inner join " +args.dbname+".tblBugReportStats on ("+args.dbname+".tblSessWebRtc.idtblSessWebRtc = "+args.dbname+".tblBugReportStats.sessWebRtcId) inner join "+args.dbname+".tblFbOutput on ("+args.dbname+".tblBugReportStats.fbOutputId = "+args.dbname+".tblFbOutput.idFbOutput) inner join "+args.dbname+".tblFBoutputDtls on ("+args.dbname+".tblFbOutput.idFbOutput ="+args.dbname+".tblFBoutputDtls.fboId and fbpTextVal is not NULL)"
	else:
		query = "select * from "+args.dbname+".tblSessWebRtc inner join " +args.dbname+".tblBugReportStats on ("+args.dbname+".tblSessWebRtc.idtblSessWebRtc = "+args.dbname+".tblBugReportStats.sessWebRtcId) inner join "+args.dbname+".tblFbOutput on ("+args.dbname+".tblBugReportStats.fbOutputId = "+args.dbname+".tblFbOutput.idFbOutput) inner join "+args.dbname+".tblFBoutputDtls on ("+args.dbname+".tblFbOutput.idFbOutput ="+args.dbname+".tblFBoutputDtls.fboId and fbpTextVal is not NULL) where idtblSessWebRtc >" + str(idWebRtc)
	df = pd.read_sql(query,conn)
	return df

def insertDatabase(conn,value):
	try:
		with conn.cursor() as cur:
			query = "update "+args.dbname+".tblConfigure set value ="+str(value)+" where searchKey = 'BUG_REPORT_LAST_READ_RECORD_ID' and isActive = 1"
			cur.execute(query)
			conn.commit()
	except pymysql.Error as e:
		print(e)
		cur.rollback()
		sys.exit(1)

def insertBugReport(conn,jira,df,pKey,assignee,priority,customfieldInfo):
	# Inserting the issue in the jira accnt, as per the specified format.
	# Header of the bug report is of the form:
	# Bug_Report_SessionID_SessKey_Name_IsHost/GlassUser_Video/Audio_Problem
	for row in df.itertuples():
		WebrtcID = row[1] #getattr(row,'idtblSessWebRtc')
		sessionKey = row[2] #getattr(row,'sessKey')
		sessionUserId = row[3] #getaatr(row,'sessUserId')
		userName = row[4] #getattr(row,'name')
		isHost = row[6] #getattr(row,'isHost')
		isGlassUser = row[7] #getattr(row,'isGlassUser')
		desc = row[21] #getattr(row,'fbpTextVal')

		# Below variables stores the stats of the session in json format.
		ptV = row[9] #getattr(row,'ptVideo')
		ptA = row[10] #getattr(row,'ptAudio')
		ptWhite = row[11] #getattr(row,'ptWhiteboard')
		ptLive = row[12] #getattr(row,'ptLiveStream')
		ptScreen = row[13] #getattr(row,'ptScreen')
		ptVideoAsset = row[14] #getattr(row,'ptVideoAssetStream')
		ptLocal = row[15] #getattr(row,'ptLocal')
		
		if isHost == 1 and isGlassUser == 0:
			Summary = "BugReport_"+str(sessionUserId)+"_"+str(sessionKey)+"_"+str(userName)+"_"+"Host"
		elif isHost == 0 and isGlassUser ==1:
			Summary = "BugReport_"+str(sessionUserId)+"_"+str(sessionKey)+"_"+str(userName)+"_"+"GlassUser"
		elif isHost == 0 and isGlassUser == 0:
			Summary = "BugReport_"+str(sessionUserId)+"_"+str(sessionKey)+"_"+str(userName)+"_"+"User"
		
		fields={
			'project':
			{
				'key':str(pKey)
			},

			customfieldInfo['sessUserID'] : str(sessionUserId),
			customfieldInfo['sessionKey'] : str(sessionKey),
			customfieldInfo['username'] : str(userName),
			customfieldInfo['statsFor'] : 'BUG_REPORT',
			customfieldInfo['WebRTCID'] : str(WebrtcID),

			# 'customfield_10025' : str(sessionUserId),
			# 'customfield_10026' : str(sessionKey),
			# 'customfield_10027' : str(userName),
			# 'customfield_10028' : 'BUG_REPORT',
			# 'customfield_10029' : str(WebrtcID),
			
			'issuetype':
			{
				'name':'Bug'
			},
			'priority':
			{
				'name':str(priority)
			},
			'description':str(desc),
			'summary': str(Summary)
		}

		try:
			# new_issue = jira.create_issue(project={'key':str(pKey)}, summary=Summary, description=desc, issuetype={'name':'Bug'},priority={'name':priority})
			new_issue = jira.create_issue(fields)
			print("Issue Id: %s" %(new_issue))
			if assignee != 'Unassigned':
				jira.assign_issue(new_issue,assignee) 
			
			# Logic for attaching files in the newly created Issue.
			if ptV is not None: #ptV represents ptVideo
				fileWrite(ptV,'ptVideo.json')
				addAttachment(jira,new_issue,'ptVideo.json')
				deleteFile('ptVideo.json')
			if ptA is not None: #ptA represents ptAudio
				fileWrite(ptA,'ptAudio.json')
				addAttachment(jira,new_issue,'ptAudio.json')
				deleteFile('ptAudio.json')
			if ptWhite is not None: #ptWhite represents ptWhiteboard
				fileWrite(ptWhite,'ptWhiteboard.json')
				addAttachment(jira,new_issue,'ptWhiteboard.json')
				deleteFile('ptWhiteboard.json')
			if ptLive is not None: #ptLive represents ptLivestream
				fileWrite(ptLive,'ptLiveStream.json')
				addAttachment(jira,new_issue,'ptLiveStream.json')
				deleteFile('ptLiveStream.json')
			if ptScreen is not None: #ptScreen represents ptScreen
				fileWrite(ptScreen,'ptScreen.json')
				addAttachment(jira,new_issue,'ptScreen.json')
				deleteFile('ptScreen.json')
			if ptVideoAsset is not None: #ptVideoAsset represents ptVideoAssetStream
				fileWrite(ptVideoAsset,'ptVideoAssetStream.json')
				addAttachment(jira,new_issue,'ptVideoAssetStream.json')
				deleteFile('ptVideoAssetStream.json')
			if ptLocal is not None: #ptLocal represents ptLocal
				fileWrite(ptLocal,'ptLocal.json')
				addAttachment(jira,new_issue,'ptLocal.json')
				deleteFile('ptLocal.json')
			# insertDatabase(conn,WebrtcID) # Again connecting to database in order to insert the idWebrtc into lastread.
		except (JIRAError,KeyboardInterrupt,SystemExit) as e:
			try:
				print(e)
				insertDatabase(conn,WebrtcID)
				return False
			except pymysql.Error as error:
				cur.rollback()
				return False
	return True

def fileWrite(data,filename):
	try:
		with open(filename,'w') as file:
			file.write(data)
	except IOError as e:
		print(e)
		sys.exit(1)

def addAttachment(jira,issuename,filename):
	try:
		with open(filename,'rb') as file:
			jira.add_attachment(issue=issuename,attachment=file)
		print("%s file attached to %s issue" %(filename,issuename))
	except (JIRAError,IOError) as e:
		print(e)
		sys.exit(1)

def deleteFile(filename):
	if os.path.isfile(filename):
		os.remove(filename)
	else:
		print("File Not Found!")

def dbConnect():
	print("Connecting To %s Database....." %(args.dbname))
	try:
		conn = pymysql.connect(args.hname,args.u,args.p,args.dbname)
		print("Connection Sucessfull")
		q = "select value from "+args.dbname+".tblConfigure where searchKey = 'BUG_REPORT_LAST_READ_RECORD_ID'"
		cur = conn.cursor()
		cur.execute(q)
		ret = cur.fetchall()
		if ret[0][0] is not '0':
			idWebRtc = ret[0][0] # if not '0' read the bug-reports after the last webrtc ID
			df = queryExecution(conn,idWebRtc) # Program will insert all the bug reports after the webrtc id if there is.
		else:
			idWebRtc = 0 # if '0' read all the bug-reports repoted till now
			df = queryExecution(conn,False) # Program will insert all the bug reports which has been reported till now
	except pymysql.Error as e:
		print(e)
		sys.exit(1)
	return (df,conn)

def main():
	config_dict = initialiseProgram()
	
	# Extracting the key,value pair from the dictionary (config_dict)
	for key,value in config_dict.items():
		# print("Key: %s Value: %s" %(key,value))
		if 'SETUP/JIRACONN/AUTH_TYPE/BASIC' == key:
			# print(key+" Line Number 279")
			jiraData=json.loads(value) # Value is in JSON format.
			username = jiraData['username']
			password = jiraData['password']
			server = jiraData['server']
		elif 'ISSUE/PROJECT_NAME' == key:
			# print(key+ " Line Number 285")
			projectName = value
		elif 'ISSUE/PROJECT_NAME/ASSIGNEE_NAME' == key:
			# print(key+ " Line number 288")
			assignee = value
		elif 'ISSUE/PROJECT_NAME/PRIORITY' == key:
			priority = value
			# print(key, " Line number 292")
		elif 'ISSUE/PROJECT_NAME/CUSTOM_FIELD_ID' == key:
			customfieldInfo=json.loads(value)
	
	# JIRA Authentication
	ret,jiraInfo = basicAuthentication(username,password,server)
	if ret == True:
		proList = projectDetails(jiraInfo)
		if len(proList) == 1:
			if (proList[0].name is not projectName):
				print("%s Not Present!" %(projectName))
			else:
				df,conn = dbConnect()
				if df.empty: 
					print("No Records Available!")
				else:
					df.columns.values[17]='cpysessKey' # changing the name of the column
					df.drop(df.columns[[16,17,19,20,21,22,23,27,28,29,31,32,33]], axis = 1,inplace=True)
					insertDatabase(conn,(df.iloc[len(df)-1].idtblSessWebRtc))
					r=insertBugReport(conn,jiraInfo,df,proList[0],assignee,priority,customfieldInfo)
					if r == True:
						print("All Bugs Inserted!")
					else:
						print("Bugs Not Inserted!")
		else:
			proList.sort(key=lambda x:x.name)
			index = -1
			index = binarySearch(projectName,proList) # checking whether the projectname ois present in the list of projects or not.
			if index is not -1:
				df,conn = dbConnect()
				if df.empty:
					print("No Records Available!")
				else:
					df.columns.values[17]='cpysessKey' # changing the name of the column
					df.drop(df.columns[[16,17,19,20,21,22,23,27,28,29,31,32,33]], axis = 1,inplace=True)
					insertDatabase(conn,(df.iloc[len(df)-1].idtblSessWebRtc))
					r=insertBugReport(conn,jiraInfo,df,proList[index],assignee,priority,customfieldInfo)
					if r == True:
						print("All Bugs Inserted!")
					else:
						print("Bugs Not Inserted Due To Error!")
			else:
				print("%s Not Present!" %(projectName))
	else:
		print(jira)

if __name__ == "__main__":
	main()
