import json

class TestResults(dict):
    testCaseResults = ""
    customData = ""
    
    def __init__(self, testCaseResults, customData):
        dict.__init__(self, testCaseResults=testCaseResults, customData=customData)