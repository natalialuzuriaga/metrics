import os
import json
import requests
from requests import exceptions
import datetime
from functools import reduce
import operator
from .constants import *

#Simple metric that can be represented by a count or value.
class SimpleMetric:
    #Url format should be in the vein of 'https://api.github.com/repos/{owner}/{repo}/issues?state=all'
    #then url.format(**data)
    def __init__(self,name,needed_parameters,endpoint_url,return_values,token = None):
        self.name = name
        self.return_values = return_values
        self.url = endpoint_url

        self.needed_parameters = needed_parameters

        if token:
            self.headers = {"Authorization": f"bearer {token}"}
        else:
            self.headers = None
    
    def get_values(self, params = None):
        if params and len(params) > 0:
            self.url = self.url.format(**params)
        

        if self.headers:
            response = requests.post(self.url,self.headers)
        else:
            response = requests.post(self.url)
        
        response_json = json.loads(response.text)
        toReturn = {}

        for val in self.return_values:
            toReturn[val] = response_json[val]
        
        return toReturn

#TODO: ask sean about committers endpoint and the data that it returns
#Think about version of simple metric that adds up all of the committers in the range

#TODO: Create class for graphql endpoint that returns a dict with all desired info

#Rest Api is worse than graphql for github.

class GraphqlMetric(SimpleMetric):
    #Return value is a dict of lists of strings that match to the keys of the dict.
    """EX:
    {
        commits_count: ["defaultBranchRef","commits","history","totalCount"]
    }
    """
    def __init__(self,name,needed_parameters,query,return_values, token = None, url = "https://api.github.com/graphql"):
        super().__init__(name,needed_parameters,url,return_values, token = token)
        self.query = query
    
    def get_values(self,params = None):
        json_dict = {
            'query' : self.query
        }

        #If there are bind variables bind them to the query here.
        if params:

            json_dict['variables'] = params
            json_dict['variables'] = json_dict['variables']
            #print(json_dict['variables'])
        
        if self.headers:
            response = requests.post(self.url,headers=self.headers,json=json_dict)
        else:
            response = requests.post(self.url,json=json_dict)
        
        response_json = json.loads(response.text)

        toReturn = {}

        #print(response_json['errors'][0]['message'])
        if "data" not in response_json.keys():
            raise requests.exceptions.InvalidJSONError(response_json['errors'][0]['message'])

        for val, keySequence in self.return_values.items():
            # Extract the nested data and store it in a flat dict to return to the user
            toReturn[val] = reduce(operator.getitem,keySequence,response_json)
        
        return toReturn

#A metric that returns a single value from a list of values
#Used for endpoints that return an iterable.
class RangeMetric(SimpleMetric):
    def __init__(self,name,needed_parameters,endpoint_url,return_values, token = None):
        super().__init__(name,needed_parameters,endpoint_url,return_values,token=token)
    
    def get_values(self,params = None):
        if params and len(params) > 0:
            self.url = self.url.format(**params)
        

        if self.headers:
            response = requests.post(self.url,self.headers)
        else:
            response = requests.post(self.url)
        
        response_json = json.loads(response.text)
        toReturn = {}

        for val in self.return_values:
            toReturn[val] = sum([item[val] for item in response_json])

        return toReturn
