from flask import Flask
from flask import request
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import json

app = Flask(__name__)

def parseIssueCreation(request_data):
    payload = request_data['issue']['fields']
    
    title = ''
    description = ''
    assignee = ''
    dueDate = ''
    status = ''
    priority = ''
    if 'summary' in  payload and payload['summary'] != None:
        title = payload['summary']
    if 'description' in payload and payload['description'] != None:
        description = payload['description']
    if 'assignee' in payload and payload['assignee'] != None:
        assignee = payload['assignee']['displayName']
    if 'duedate' in payload and payload['duedate'] != None:
        dueDate = payload['duedate']
    if 'status' in payload and payload['status'] != None:
        status = payload['status']['name']
    if 'priority' in payload and payload['priority'] != None: 
        priority = payload['priority']['name']
        
    pprint(title)
    pprint(description)
    pprint(assignee)
    pprint(dueDate)
    pprint(status)
    print(priority)
    
def parseIssueUpdate(payload):
    pprint("in issue update")
    
def parseIssueDeleted(payload):
    pprint("in issue delete")
    
@app.route('/jiraWebHook', methods=['POST'])
def webHookJira():
    request_data = request.get_json()
    
    webHookEvent = request_data['webhookEvent']
    match webHookEvent:
        case "jira:issue_created":
            parseIssueCreation(request_data)
        case "jira:issue_updated":
            parseIssueUpdate(request_data)
        case "jira:issue_deleted":
            parseIssueDeleted(request_data)
        case _:
            pprint("Not recognized Web Hook Event")
            
    return ''

if __name__ == "__main__":
    app.run(debug=True)

