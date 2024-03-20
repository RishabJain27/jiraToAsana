from flask import Flask
from flask import request
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
import asana
from asana.rest import ApiException

app = Flask(__name__)

configuration = asana.Configuration()
configuration.access_token = '2/1206848302395917/1206874990632238:b503b349b4150c8f73c0b5c01d1ec69c'
api_client = asana.ApiClient(configuration)
tasks_api_instance = asana.TasksApi(api_client)


def getWebProductionTasks():
    work_production_gid = "1206848441607075"
    opts = {}
    listTaskNames = []
    listMilestoneNames = []
    try: 
        # Get tasks from a project
        api_response = tasks_api_instance.get_tasks_for_project(work_production_gid, opts)
        for data in api_response:
            if data['resource_subtype'] == 'default_task':
                listTaskNames.append(data['name'])
            if data['resource_subtype'] == 'milestone':
                listMilestoneNames.append(data['name'])
    except ApiException as e:
        pprint("Exception when calling TasksApi->get_tasks_for_project: %s\n" % e)
    
    return listTaskNames, listMilestoneNames
    
def createAsanaTask(title, description, assignee, dueDate, status, priority):
    pprint("create Task")
    listTaskNames, listMileStoneNames = getWebProductionTasks()
    pprint(listTaskNames)
    pprint(listMileStoneNames)

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
        
    createAsanaTask(title, description, assignee, dueDate, status, priority)
    
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

