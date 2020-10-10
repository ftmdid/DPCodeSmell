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
    projectName="django"
    downloads = download.Downloads(projectName)
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
    
    
    projectName='django'
    analysis=analysis.Analysis(projectName)
    analysis.makeSemanticAndSyntacticAnalysis()
    
    projectName='numpy'
    analysis=analysis.Analysis(projectName)
    analysis.makeSemanticAndSyntacticAnalysis()
    
    projectName='zulip'
    analysis=analysis.Analysis(projectName)
    analysis.makeSemanticAndSyntacticAnalysis()
    
    projectName='keras'
    analysis=analysis.Analysis(projectName)
    analysis.makeSemanticAndSyntacticAnalysis()
    
    projectName='models'
    analysis=analysis.Analysis(projectName)
    analysis.makeSemanticAndSyntacticAnalysis()

#----------------------------------------------------------------------#
    projectName="numpy"   
    relation=relation.Relation(projectName)   
    relation.checkForRelation()  
    
    projectName="django"   
    relation=relation.Relation(projectName)   
    relation.checkForRelation()  
    
    projectName="zulip"   
    relation=relation.Relation(projectName)   
    relation.checkForRelation()  
    
    projectName="keras"   
    relation=relation.Relation(projectName)   
    relation.checkForRelation()  
    
    projectName="models"   
    relation=relation.Relation(projectName)   
    relation.checkForRelation()
    
    print("Done with Downloading!")