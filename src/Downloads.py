'''
Created on Jun 10, 2020

@author: Neda
'''

import os
import git
import src.FileOperations as FO

import requests
import csv
from ratelimit import limits, sleep_and_retry
import src.GitLogs as GL


class Downloads(object):
    def __init__(self,projectName):    
        """
            Constructor
        """
        self.projectName=projectName
        self.gitOp = GL.GitLogs(self.projectName)
        self.fileOp= FO.FileOperations(self.projectName)
        

    def downloadGitHubPythonProject(self):

        gitURL= self.fileOp.getGitHubURL()
        #gitLogOp= GL.GitLogs()
     
        cloneDir = os.path.dirname(os.path.dirname(__file__)) +self.fileOp.getDirURLToClone()
        
        # if there are files under the clones directory, delete the files to download it again
        self.fileOp.removeFilesInDir(cloneDir)
             
        # Download the github url       
        git.Git(cloneDir).clone(gitURL + self.fileOp.getGitRepoURL())
        print(self.projectName+" project is downloaded!")
    

    def downloadCommits(self):
        
        self.downloadGitHubPythonProject()
        cloneDir = os.path.dirname(os.path.dirname(__file__)) +self.fileOp.getDirURLToClone()
        # Get git log reports
        """
            %h -- abbreviated commit hash
            %p -- abbreviated parent hash
            %an -- Author name
            %ad -- author date
            %ae -- author email
            %cn -- committer name
            %ce -- committer email
            %cd -- committer date
            %s -- subject
            --name-status --> show the list of files affected with added/modified/deleted information as well (A=Added, D=Deleted, M=Modified, R=Renamed)
        """
        
        for fileInDir in os.listdir(cloneDir):
                dirToGetGitLog=os.path.join(cloneDir,fileInDir) #['cHash','pHash', 'aName', 'aEmail','aDate', 'cName','cEmail','cDate','subject']
                hexshas2 = git.Git(dirToGetGitLog).log('--log-size','--name-status', '--pretty=format:~||~%h~||~%p~||~%an~||~%ae~||~%ad~||~%cn~||~%ce~||~%cd~||~%s~||~')
        
        print(self.projectName+" project log is downloaded!")  
        self.gitOp.writeDataToCSVLogFile(hexshas2)    
        return hexshas2
        print(self.projectName+" project log is written to csv file!")
        
    def downloadModifiedPythonFiles(self):
        hexshas=self.downloadCommits()
          
        #Create the modified file list
        #filesList has the files that are modified like [commitId, 'M', fileNameWithURL,date]
        filesList = self.gitOp.createModifiedFileList(hexshas) 
        
        
        
        # try - except statement reads the commit id and url of files and save it in the util/Python/numpy folder
        self.fileOp.createCopyOfModifiedPythonFilesInFolder(filesList,self.projectName.lower())
            
        print ("Modified python files are downloaded!")

        
        
    def downloadIssuesFromIssueTrackingSys(self,projectURL,numberOfPages):
        try:
            url = projectURL
            projectPath = os.path.dirname(os.path.dirname(__file__))+ '/util/issues/issues'       
            csvfile = 'issuesOf'+self.projectName+".csv"
            csvout = csv.writer(open(os.path.join(projectPath,csvfile), 'w+'))
            csvout.writerow(('id', 'Title', 'Body',"User", 'Label','Created At', 'Updated At'))
            for j in range(1,numberOfPages):
                #url= url[:66]+str(j)+url[66:] #numpy - zulip
                #url= url[:68]+str(j)+url[68:]#django
                #url= url[:71]+str(j)+url[71:] #Keras-team
                #url= url[:72]+str(j)+url[72:] #models
                url= url[:80]+str(j)+url[80:] #scikit-learn
                print(url)
    
                FIFTEEN_MINUTES = 1200 #It was 900
                @sleep_and_retry
                @limits(calls=20, period=FIFTEEN_MINUTES)  # the calls was 15
                def call_api(url):    
                    response = requests.get(url) 
                    if not response.status_code ==200:
                        raise Exception(response.status_code)
                    return response
                
                response=call_api(url)
                i=0
                for issue in response.json():
                    
                    print("issue number: "+str(i))
                    
                    issueLabels=[]
                    labels=issue['labels']
                    if len(labels)>1:
                        for k in  range(len(labels)):
                            print("Number of labels: "+str(k))
                            issueLabels.append(labels[k]['name'].encode('utf-8') if labels[k]['name'] else labels[k]['name']) # if statement is added for None type object cannot be encoded!
                    elif len(labels)==1:
                        issueLabels.append(labels[0]['name'].encode('utf-8') if labels[0]['name'] else labels[0]['name'])
                   
    
                    
                    if len(issueLabels)>=1:
                       
                        csvout.writerow([issue['number'], 
                                        str(issue['title'].encode('utf-8').decode('utf-8')) if issue['title'] else issue['title'],\
                                        str(issue['body'].encode('utf-8').decode('utf-8')) if issue['body'] else issue['body'],\
                                        str(issue['user']['login'].encode('utf-8').decode('utf-8')) if issue['user']['login'] else issue['user']['login'],\
                                        b" ".join(issueLabels),\
                                        issue['created_at'], issue['updated_at']])
                    else:
                        csvout.writerow([issue['number'],\
                                        str(issue['title'].encode('utf-8').decode('utf-8')) if issue['title'] else issue['title'],\
                                        str(issue['body'].encode('utf-8').decode('utf-8')) if issue['body'] else issue['body'],\
                                        str(issue['user']['login'].encode('utf-8').decode('utf-8') if issue['user']['login'] else issue['user']['login']),\
                                        "None",\
                                        issue['created_at'], issue['updated_at']]) # if statement is for None type object cannot be encoded!
                    i +=1
    
                url=projectUrl 
    
        except IOError or Exception or AttributeError as ex:
            print(str(ex))
        print("Done")


if __name__ == '__main__':
    #projectName='zulip'
    #projectName='keras'
    #projectName='numpy'
    #projectName='models'
    #projectName="django"
    projectName="scikit-learn"
    downloads=Downloads(projectName)
    #projectUrl="https://api.github.com/repos/keras-team/keras/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/zulip/zulip/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/django/django/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/numpy/numpy/issues?state=closed&page=&per_page=100"
    #projectUrl= "https://api.github.com/repos/tensorflow/models/issues?state=closed&page=&per_page=100"
    projectUrl = "https://api.github.com/repos/scikit-learn/scikit-learn/issues?state=closed&page=&per_page=100"
    numberOfPages=165
    #downloads.downloadGitHubPythonProject()
    #downloads.downloadCommits()
    #downloads.downloadModifiedPythonFiles()
    downloads.downloadIssuesFromIssueTrackingSys(projectUrl, numberOfPages)
    
    print("Done with Downloading!")
 

