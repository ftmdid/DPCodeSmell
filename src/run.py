'''
Created on Oct 10, 2020

@author: neda
'''
#import Downloads as download
import src.Analysis as analysis

import src.Relation as relation


  
if __name__ == '__main__':
    
    #projectName='zulip'
    #projectName='keras'
    #projectName='numpy'
    #projectName='models'
    #projectName="django"
    #projectName="scikit-learn"
    #downloads = download.Downloads(projectName)
    #projectUrl="https://api.github.com/repos/keras-team/keras/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/zulip/zulip/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/django/django/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/numpy/numpy/issues?state=closed&page=&per_page=100"
    #projectUrl= "https://api.github.com/repos/tensorflow/models/issues?state=closed&page=&per_page=100"
    #projectUrl= "https://api.github.com/repos/scikit-learn/scikit-learn/issues?state=closed&page=&per_page=100"
    
    #numberOfPages=164
    #downloads.downloadGitHubPythonProject()
    #downloads.downloadCommits()
    #downloads.downloadModifiedPythonFiles()
    #downloads.downloadIssuesFromIssueTrackingSys(projectUrl, numberOfPages)
    #projectName='Django'
    
    '''
    projectName='django'
    print("Started analysis on "+projectName)
    anlysis=analysis.Analysis(projectName)
    anlysis.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''
    '''
    projectName='zulip'
    print("Started analysis on "+projectName)
    analysis3=analysis.Analysis(projectName)
    analysis3.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''
    '''
    projectName='keras'
    print("Started analysis on "+projectName)
    analysis4=analysis.Analysis(projectName)
    analysis4.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''
    '''
    projectName='models'
    analysis5=analysis.Analysis(projectName)
    analysis5.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''
    '''
    projectName='numpy'
    print("Started analysis on "+projectName)
    analysis2=analysis.Analysis(projectName)
    analysis2.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''
    '''
    projectName='scikit-learn'
    print("Started analysis on "+projectName)
    analysis6=analysis.Analysis(projectName)
    analysis6.makeSemanticAndSyntacticAnalysis()
    print("Finished analysis on "+projectName)
    '''

#----------------------------------------------------------------------#
 
  

    '''
    projectName="django"   
    print("Started bad smell analysis on "+projectName)
    relation2=relation.Relation(projectName)   
    relation2.checkForRelation() 
    print("Finished bad smell analysis on "+projectName) 
'''


    '''
    projectName="scikit-learn"   
    print("Started bad smell analysis on "+projectName)
    relation2=relation.Relation(projectName)   
    relation2.checkForRelation() 
    print("Finished bad smell analysis on "+projectName)
    '''
    '''
    projectName="keras"   
    print("Started bad smell analysis on "+projectName)
    relation4=relation.Relation(projectName)   
    relation4.checkForRelation()  
    print("Finished bad smell analysis on "+projectName) 
    '''
    '''
    projectName="models"   
    print("Started bad smell analysis on "+projectName)
    relation5=relation.Relation(projectName)   
    relation5.checkForRelation()
    print("Finished bad smell analysis on "+projectName) 
    '''
    #'''
    projectName="numpy"   
    print("Started bad smell analysis on "+projectName)
    relat=relation.Relation(projectName)  
    relat.checkForRelation()
    print("Finished bad smell analysis on "+projectName)
    #'''
    #'''
    projectName="zulip"   
    print("Started bad smell analysis on "+projectName)
    relation3=relation.Relation(projectName)   
    relation3.checkForRelation()  
    print("Finished bad smell analysis on "+projectName) 
    #'''
            
    print("Done with Downloading!")
    