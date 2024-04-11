from flask import Blueprint
from flask import request
from flask import Response
import asana
import requests
from asana.rest import ApiException
from requests.auth import HTTPBasicAuth
from pprint import pprint
import json
import threading

asana_routes = Blueprint('asana_routes', __name__)

#Asana API configurations
configuration = asana.Configuration()
configuration.access_token = '<API TOKEN>'
api_client = asana.ApiClient(configuration)
tasks_api_instance = asana.TasksApi(api_client)

#Jira API configurations
jira_url = "https://442561275-team-mcpys4njze6e.atlassian.net/rest/api/3/"
auth = HTTPBasicAuth("alan-phnx@442561275.asanatest1.us", "<API TOKEN>")
headers = {
    "Accept": "application/json"
}

#API call to Asana to get Task information and return jiraId associated with Task
#returns None object if no jiraId associated with Asana Task
def getTaskDataNoJiraId(gid):
    taskData = getTaskFromId(gid)
    if taskData is None:
        return
    
    for field in taskData['custom_fields']:
        if field['name'] == 'jiraID':
            if field['display_value'] is None or field['display_value'] == '':
                return taskData
    
    return None

#API call to Asana to get Task given Task gid
def getTaskFromId(gid):
    try:
        # Get a task
        taskData = tasks_api_instance.get_task(gid, {})
        return taskData
    except ApiException as e:
        pprint("Exception when calling TasksApi->get_task: %s\n" % gid)
        return None
    
#API call to Asana to update Task given task gid and data containing updated values
def updateTask(taskId, data):
    body = {"data": data}
    opts = {}
    
    try:
        # Update a task
        response = tasks_api_instance.update_task(body, taskId, opts)
    except Exception as e:
        pprint("Exception when calling TasksApi->update_task: %s\n" % e)
        
#API call to Asana to get all Task's gid associated with Web Production Requests Project
def getWebProductionTasks():
    work_production_gid = "1206848441607075"
    opts = {}
    
    try: 
        # Get tasks from a project
        api_response = tasks_api_instance.get_tasks_for_project(work_production_gid, opts)
        return api_response
    except ApiException as e:
        pprint("Exception when calling TasksApi->get_tasks_for_project: %s\n" % e)
    
    return []

#API call to Jira to get Jira Issue given Asana Task ID
def getJiraTaskByAsanaId(taskId):
    # Gets All Valid Tasks From Jira
    issueRequest = jira_url + "search"
    
    #Only get Task Types with Asana Id from Project
    jql = 'project = "Go to market sample" and "asanaid[short text]" ~ "' + taskId + '" ORDER BY created DESC'
    query = {
        'jql': jql
    }
    
    try:
        response = requests.request(
            "GET",
            issueRequest,
            headers=headers,
            params=query,
            auth=auth
        )
        json_response = json.loads(response.text)
        return json_response
    except ApiException as e:
        pprint("Exception when calling Jira Task Search: %s\n" % e)
        return None

#API call to Jira to delete Jira Issue given jiraId/key
def deleteJiraIssue(jiraId):
    issueUrl = jira_url + 'issue/' + jiraId
    
    response = requests.request(
        "DELETE",
        issueUrl,
        auth=auth
    )

# API call to Jira to get latest comment on Issue
def getLatestJiraComment(id):
    commentUrl = jira_url + 'issue/' + id + '/comment'
    
    response = requests.request(
    "GET",
    commentUrl,
    headers=headers,
    auth=auth
    )
    response = json.loads(response.text)

#API call to Jira to create Comment on Issue
def createJiraComments(id, property, data):
    lastComment = ''
    try:
        lastComment = str(getLatestJiraComment(id))
    except Exception as e:
        print("error getting latest comment")
        
    commentUrl = jira_url + 'issue/' + id + '/comment'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    #Format comment depending on property value
    comment = ""
    if property == 'summary': 
        comment += "Changed Title/Summary to " + data
    elif property == 'description':
        comment += "Changed the description "
        if(data is not None or data != None):
            comment += " to " +  str(data['content'][0]['content'][0]['text'])
    elif property == 'assignee':
        if data == None or data is None:
            name = 'No assignee'
        else:
            userNameToIdMap = {"712020:7b0b4b10-52e5-43c6-b5da-c168422a0c16" : "Alan Wang", "712020:68a6843e-1d90-4261-bbd3-592fdcd0690c" : "Charlie Roshan" }
            name = userNameToIdMap.get(data)
        comment += "Changed Assignee to " + name
    elif property == 'duedate':
        if data == None or data is None:
            date = 'No due date'
        else:
            date = data
        comment += "Changed Due date to " + date
    elif property == 'priority':
        priorityMap = {"1" : "Highest", "2" : "High", "3" : "Medium", "4" : "Low", "5" : "Lowest"}
        comment += "Changed priority to " + priorityMap.get(data)
    elif property == 'status':
        #Mapping Jira Id to Name
        statusMap = {"21" : "To Do", "31" : "In Progress", "41" : "Ready for Launch", "51" : "Launched"}
        comment += "Changed status to " + statusMap.get(data)
    else:
        return

    #Avoid duplicates
    if str(comment) == str(lastComment):
        return
    
    payload = json.dumps( {
    "body": {
        "content": [
        {
            "content": [
            {
                "text": comment,
                "type": "text"
            }
            ],
            "type": "paragraph"
        }
        ],
        "type": "doc",
        "version": 1
    }
    } )

    response = requests.request(
        "POST",
        commentUrl,
        data=payload,
        headers=headers,
        auth=auth
    )

#API call to Jira to update Task when updating a user change
def updateIssueUser(id, userId):
    issueUrl = jira_url + 'issue/' + id + '/assignee'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps( {
        "accountId": userId        
    })
    response = requests.request(
        "PUT",
        issueUrl,
        data=payload,
        headers=headers,
        auth=auth
    )

#API call to Jira to update Workflow state (To Do, In Progress, Ready for Launch, Launched)
def transitionJiraIssue(id, propertyKey, data):
    issueUrl = jira_url + 'issue/' + id + '/transitions'
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps({ "transition": {propertyKey: data}})
    try: 
        request_response = requests.request(
            "POST",
            issueUrl,
            data=payload,
            headers=headers,
            auth=auth
        )
        #Create Comment with updated status
        createJiraComments(id, "status", data)
    except requests.exceptions.HTTPError as err:
        print("Error updating Jira Issue : %s" % err.args[0])

#API call to Jira to update Issue(Issue, Bug, Epic)
def updateJiraIssue(id, propertyKey, payload):
    issueUrl = jira_url + 'issue/' + id
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps({ "fields": {propertyKey: payload}})
    try: 
        request_response = requests.request(
            "PUT",
            issueUrl,
            data=payload,
            headers=headers,
            auth=auth
        )
    except requests.exceptions.HTTPError as err:
        print("Error updating Jira Issue : %s" % err.args[0])

#API call to create Jira issue provided necessary values        
def createJiraIssue(gid, title, description, assignee, due_date, status, priority, type):
    # Edit information for Jira
    userNameToIdMap = {"Alan Wang" : "712020:7b0b4b10-52e5-43c6-b5da-c168422a0c16", "Charlie Roshan" : "712020:68a6843e-1d90-4261-bbd3-592fdcd0690c"}
    if assignee is not None:
        assignee = userNameToIdMap.get(assignee)
    
    issueTypeMap = {"default_task": "10005", "milestone": "10009"}
    typeId = issueTypeMap.get(type)
    
    priorityMap = {"High" : "2", "Medium" : "3", "Low" : "4", "Lowest" : "5", "Highest" : "1"}
    if priority is not None:    
        priority = priorityMap.get(priority)
    else:
        priority = "3" #set to medium be default
            
    issueUrl = jira_url + 'issue'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = json.dumps({
        "fields": {
            "project": {
                "id": "10001"
            },
            "assignee": {
                "id": assignee
            }, 
            "description": {
                "content": [
                    {
                    "content": [
                        {
                        "text": description,
                        "type": "text"
                        }
                    ],
                    "type": "paragraph"
                    }
                ],
                "type": "doc",
                "version": 1
            },
            "duedate": due_date,
            "summary": title,
            "issuetype": {
                "id": typeId
            },
            "priority" : {
                "id": priority
            },
            "customfield_10035": gid
        }
    })
    
    try:
        response = requests.request(
            "POST",
            issueUrl,
            data=payload,
            headers=headers,
            auth=auth
        )
        response = json.loads(response.text) 
        return response['key']
    
    except requests.exceptions.HTTPError as err:
        print("Error creating Jira Issue : %s" % err.args[0])

# Finds field in Asana Task and returns field value
# Return True/False whether that field exits in Task Data
def parseTaskDataByField(taskData, field):
    if taskData is None or field is None:
        return False, None
    
    if field == "notes":
        return True, taskData['notes']
    elif field == "name":
        return True, taskData['name']
    elif field == 'assignee':
        if taskData['assignee'] is not None:
            return True, taskData['assignee']['name'] #assigned to a Person
        else:
            return True, None #unassigned
    elif field == 'due_on':
        return True, taskData['due_on'] 

    return False, None

#Get Task field resource from Asana Task given TaskId and field name    
def getNewTaskResource(taskId, field):
    if taskId is None:
        return False, None
    
    taskData = getTaskFromId(taskId)
    
    if taskData is None:
        return False, None
    else:
        return parseTaskDataByField(taskData, field)
        
#Sets Jira Notes Field with updated value
def setJiraNotesField(newValue):
    newDesc = {
        "content": [
        {
        "content": [
            {
            "text": newValue,
            "type": "text"
            }
        ],
        "type": "paragraph"
        }
    ],
    "type": "doc",
    "version": 1
    }
    return newDesc
    

#Helper function to get assignee Id
def setJiraAssigneeField(assignee):
    mapJiraToAsanaNames = {"Alan Wang" : "712020:7b0b4b10-52e5-43c6-b5da-c168422a0c16", "Charlie Roshan" : "712020:68a6843e-1d90-4261-bbd3-592fdcd0690c"}
    assignee = mapJiraToAsanaNames.get(assignee)
    if assignee != '' or assignee is not None: 
        return assignee
    else:
        return None

#Parses Jira issue given field value and returns new Jira value            
def parseJiraIssue(issue, field, newValue):
    if field == "notes":
        description = issue['fields']['description']
        description = setJiraNotesField(newValue)
        return "description", description
    elif field == 'name':
        summary = newValue
        return "summary", summary
    elif field == 'assignee':
        assignee = setJiraAssigneeField(newValue)
        return 'assignee', assignee
    elif field == 'due_on':
        dueDate = newValue
        return 'duedate', dueDate

    return '', ''

#Filters Jira task to get new value given resource name    
def filterJiraTask(taskId, field, newValue):
    jiraTask = getJiraTaskByAsanaId(taskId)
    issues = jiraTask['issues']
    for issue in issues:
        property, data = parseJiraIssue(issue, field, newValue)
        createJiraComments(issue['id'], property, data)
        if property == 'assignee':
            updateIssueUser(issue['id'], data)
            # No valid user in Jira set assignee in Asana to know
            # Keeps Jira and Asana synced
            if data is None:
                updateTask(taskId, {"assignee" : data})
        else: 
            updateJiraIssue(issue['id'], property, data)

#Get Jira Priority Key from Asana            
def convertAsanaPriorityToJira(asanaId):
    priorityMap = {"1206874810766684" : "2", "1206874810766685" : "3", "1206874810766686" : "4", "1206874810766687" : "5", "1206874810766688" : "1"}
    
    jiraPriorityId = priorityMap.get(asanaId)
    return jiraPriorityId

#Parse response from Asana GET Task and return relevant information
def parseAsanaTask(task):
    gid = None
    title = None
    description = None
    assignee = None 
    due_date = None
    status = None
    priority = None
    type = None
    jiraId = None
    
    gid = task['gid']
    if 'name' in task and task['name'] != None:
        title = task['name']
    if 'notes' in task and task['notes'] != None:
        description = task['notes']
    if 'assignee' in task and task['assignee'] != None:
        assignee = task['assignee']['name']
    if 'due_on' in task and task['due_on'] != None:
        due_date = task['due_on']
    if 'memberships' in task and task['memberships'] != None:
        for membership in task['memberships']:
            if 'section' in membership and membership['section'] != None:
                status = membership['section']['name']   
    if 'custom_fields' in task and task['custom_fields'] != None:
        for field in task['custom_fields']:
            if field['name'] == 'Priority':
                priority = field['display_value']
            if field['name'] == 'jiraID':
                jiraId = field['display_value']
                
    if 'resource_subtype' in task and task['resource_subtype'] != None:
        type = task['resource_subtype']          
    
    return gid, title, description, assignee, due_date, status, priority, type, jiraId

#Web Hook for Changes for default/Milestone Task
@asana_routes.route("/asanaWebHook", methods=['POST'])
def asanaWebHook():
    # Multithreading function to avoid timeout
    # API response will return 200 Ok while Asana tasks continuing to be created
    request_data = request.get_json()
    def long_running_Task(**kwargs):
        request_data = kwargs.get('request_data', {})
        if request_data['events'] != None:
            for event in request_data['events']:
                valid = False
                taskId = None
                field = None
                
                try :
                    if event['resource'] != None:
                        taskId = event['resource']['gid']
                    
                    if event['change'] != None:
                        field = event['change']['field']
                        
                    if field != None and field == 'custom_fields': #special case for Priority field
                        if event['change']['new_value'] != None and event['change']['new_value']['enum_value'] != None:
                            newPriorityValue = event['change']['new_value']['enum_value']['gid']
                            jiraTask = getJiraTaskByAsanaId(taskId)
                            issues = jiraTask['issues']
                            for issue in issues:
                                priorityId = convertAsanaPriorityToJira(newPriorityValue)
                                updateJiraIssue(issue['id'], "priority", {"id" : priorityId})
                                createJiraComments(issue['id'], "priority", priorityId)
                    else:
                        valid, newValue = getNewTaskResource(taskId, field)
                        if valid:
                            filterJiraTask(taskId, field, newValue)
                except Exception as e:
                    print("Error parsing incoming Asana WebHook Information %s" % repr(e))
                    
    thread = threading.Thread(target=long_running_Task, kwargs={
        'request_data': request_data})
    thread.start()
    return {}

#Web Hook for Deleting a Task/Milestone
@asana_routes.route("/asanaWebHookDelete", methods=['POST'])
def asanaWebHookDelete():
    request_data = request.get_json()
    if request_data['events'] != None:
        for event in request_data['events']:
            taskId = None
            if event['resource'] != None:
                taskId = event['resource']['gid']
            
            if taskId != None:
                jiraIssue = getJiraTaskByAsanaId(taskId)
                issues = jiraIssue['issues']
                for issue in issues:
                    deleteJiraIssue(issue['id'])
    return {}

#Web Hook for Sections(New Requests, In Active Sprint, Completed, Launched)
@asana_routes.route("/asanaWebHookSection", methods=['POST'])
def asanaWebHookSection(): 
    request_data = request.get_json()
    
    try:
        for event in request_data['events']:
            
            if event['parent'] != None:
                taskId = event['parent']['gid']
            
            if taskId != None:
                asanaTask = getTaskFromId(taskId)
                gid, title, description, assignee, due_date, status, priority, type, jiraId = parseAsanaTask(asanaTask)
                
                statusMap = {"New Requests" : "21", "In Active Sprint": "31", "Complete": "41", "Launched" : "51"}
                status = statusMap.get(status)
                
                if jiraId != None:
                    transitionJiraIssue(jiraId, "id", status)
    except Exception as e:
        print("Error Parsing Section Added Request")
    return {}    

#Web Hook for Adding Asana Task
@asana_routes.route("/asanaWebHookCreate", methods=['POST'])
def asanaWebHookCreate():
    request_data = request.get_json()
    try:
        for event in request_data['events']:
            taskId = event['resource']['gid']
            
            asanaTask = getTaskFromId(taskId)
            gid, title, description, assignee, due_date, status, priority, type, jiraId = parseAsanaTask(asanaTask)

            if jiraId == None:
                jiraId = createJiraIssue(gid, title, description, assignee, due_date, status, priority, type)
                
                #Get Jira Id for status update
                statusMap = {"New Requests" : "21", "In Active Sprint": "31", "Complete": "41", "Launched" : "51"}
                status = statusMap.get(status)
                #Update Jira Status    
                transitionJiraIssue(jiraId, "id", status)
                #Update Asana Task with newly created Jira Task
                updateTask(gid, {"custom_fields":{"1206894227644145" : jiraId}})
    except Exception as e:
        print("Error Parsing Creating Task Request")
    return {}

#Create Asana Tasks in Jira
@asana_routes.route("/syncToJira", methods=['GET'])
def syncToJira():
    listAsanaTasks = list(getWebProductionTasks())
    
    #Multithreading function to avoid timeout
    #API response will return 200 Ok while Jira issues continuing to be created
    def long_running_Task(**kwargs):
        
        listAsanaTasks = kwargs.get('listAsanaTasks', {})
        listAsanaTaskToCreate = []
        for asanaTask in listAsanaTasks:
            task = getTaskDataNoJiraId(asanaTask['gid'])
            if task is not None:
                listAsanaTaskToCreate.append(task)
        
        for asanaTask in listAsanaTaskToCreate:
            gid, title, description, assignee, due_date, status, priority, type, jiraId = parseAsanaTask(asanaTask)
            jiraId = createJiraIssue(gid, title, description, assignee, due_date, status, priority, type)
            
            #Get Jira Id for status update
            statusMap = {"New Requests" : "21", "In Active Sprint": "31", "Complete": "41", "Launched" : "51"}
            if status is not None:
                status = statusMap.get(status)
            #Update Jira Status    
            transitionJiraIssue(jiraId, "id", status)
            #Update Asana Task with newly created Jira Task
            updateTask(gid, {"custom_fields":{"1206894227644145" : jiraId}})
    
    thread = threading.Thread(target=long_running_Task, kwargs={
        'listAsanaTasks': listAsanaTasks})
    thread.start()
    
    return {}