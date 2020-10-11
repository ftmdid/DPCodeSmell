'''
Created on Oct 10, 2020

@author: neda
'''
import src.Downloads as download
import src.Analysis as analysis
import src.Relation as relation
if __name__ == '__main__':
    
    #projectName='zulip'
    #projectName='keras'
    #projectName='numpy'
    #projectName='models'
    #projectName="django"
    #downloads = download.Downloads(projectName)
    #projectUrl="https://api.github.com/repos/keras-team/keras/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/zulip/zulip/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/django/django/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/numpy/numpy/issues?state=closed&page=&per_page=100"
    #projectUrl= "https://api.github.com/repos/tensorflow/models/issues?state=closed&page=&per_page=100"
    
    #numberOfPages=160
    #downloads.downloadGitHubPythonProject()
    #downloads.downloadCommits()
    #downloads.downloadModifiedPythonFiles()
    #downloads.downloadIssuesFromIssueTrackingSys(projectUrl, numberOfPages)
    #projectName='Django'
    
#     
#     projectName='django'
#     anlysis=analysis.Analysis(projectName)
#     anlysis.makeSemanticAndSyntacticAnalysis()
#     
#     projectName='numpy'
#     analysis2=analysis.Analysis(projectName)
#     analysis2.makeSemanticAndSyntacticAnalysis()
#     
#     projectName='zulip'
#     analysis3=analysis.Analysis(projectName)
#     analysis3.makeSemanticAndSyntacticAnalysis()
#      
#     projectName='keras'
#     analysis4=analysis.Analysis(projectName)
#     analysis4.makeSemanticAndSyntacticAnalysis()
#      
#     projectName='models'
#     analysis5=analysis.Analysis(projectName)
#     analysis5.makeSemanticAndSyntacticAnalysis()

#----------------------------------------------------------------------#
# 
#     projectName="numpy"   
#     relat=relation.Relation(projectName)   
#     relat.checkForRelation()  
#     
#     projectName="django"   
#     relation2=relation.Relation(projectName)   
#     relation2.checkForRelation()  
#      
#     projectName="zulip"   
#     relation3=relation.Relation(projectName)   
#     relation3.checkForRelation()  
#      
#     projectName="keras"   
#     relation4=relation.Relation(projectName)   
#     relation4.checkForRelation()  
#      
#     projectName="models"   
#     relation5=relation.Relation(projectName)   
#     relation5.checkForRelation()
    import matplotlib.pyplot as plt
    import os
    import csv
    fileName=os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/BadSmells/LargeClassRelationAnalysisOfkeras.csv'
    
  
    folderList={}
    with open(fileName) as fle:
        csvReader= csv.reader(fle, delimiter=",")
        rowCount=0
        
        for row in csvReader:
            if rowCount!=0:
                if int(row[5])-int(row[4])>-1 and int(row[5])-int(row[4])<5:
                       
                        if not row[7] in folderList.keys():
                            folderList[row[7]]={}
                            classList={}
                            classList[row[2]]=[int(row[5])-int(row[4])]
                            temp=row[1]
                            folderList[row[7]]=classList
                        else:
                            for key, value in folderList.items():
                                if not row[2] in folderList[key].keys():                       
                                    folderList[key][row[2]]=[int(row[5])-int(row[4])]
                                else:
                                    if not int(row[5])-int(row[4]) in folderList[key][row[2]]:
                                        folderList[key][row[2]].append(int(row[5])-int(row[4]))
                          
            rowCount +=1
   

    for key, value in folderList.items():
        print(key, value)

    
    
    
      
    
    
    print("Done with Downloading!")
    