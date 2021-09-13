
import src.smell.longMethodSmell as lMethod
import os
import ast
import inspect
projectPath =   projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/Validation/ToolValidation/allPythonFiles.py')
parsedFile =  lMethod.parseFile(projectPath)
parsedFileContent = list(ast.walk(parsedFile))
for content in parsedFileContent:
    caller=None
    #depth =0
    if isinstance(content, ast.FunctionDef):
        caller =inspect.stack(content)
        # while True:
        #    # search for the correct calling method
        #    caller = getframeinfo(stack()[depth][0])
        #    if caller.function != 'trace' or depth >= 6:
        #        break
        #    depth += 1
        print(caller.filename, caller.lineno, caller.function, None)