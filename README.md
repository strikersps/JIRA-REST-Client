# JIRA REST Client

Developed a **REST Client** which extracts the Bug Report from the MySQL Database first and then log all the _Bug Reports_ with relevant stats (JSON Format) to specific JIRA Project using REST API provided by JIRA.  

#### System Requirements:
* Ubuntu 16.04 LTS or later.   
* Python 2.7 or 3.   
* JIRA and all the dependencies must be installed.   

#### Installation:

* Run the following command to install all the packages:  
	```bash
	sudo pip3 install -r packages.txt
	sudo apt-get install python3-pandas
	```

For more information on installing dependencies, refer the link: [JIRA Installation](https://jira.readthedocs.io/en/master/installation.html)  

* To check whether JIRA is installed successfully or not:  
Open the terminal:  
	``` python
	python3    
	from jira import JIRA
	```
If no error is reported by the interpreter, means JIRA is sucessfully installed.  

#### Execution of the Code:

* After sucessfull installtion, issue the following command in the terminal as the program has a command line interface.  
	``python3 jira_rest_client.py -dbname databasename -hname hostname -u username -p password``  

* There are 4 arguments which you must pass (in any order) as a command line argument:  
1. -dbname: Name of the database.  
2. -hname: Hostname of the database.  
3. -u: username of the database.  
4. -p: password of the database.  

``E.g. python3 jira_rest_client.py -dbname localhost -hname 127.0.0.1 -u abcdef -p 12345678``  

#### References:
* For more information on **"How The REST Client Works"**, refer the link:  
[How The REST Client Works](https://docs.google.com/document/d/1CHUcDlvIS7zXKYXRY1dFw2VWpx4xE4YB63O0jG0dfM8/edit?usp=sharing)  

* For more information on **"Python JIRA REST API"**, refer the link:  
[Python JIRA REST API](https://jira.readthedocs.io/en/master/api.html)  

