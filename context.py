import Glassdoor
import Website_Class
import pymongo
import pandas as pd
import os
import CountryGrouping
import Heuristic_model
import us
import linkedin_scraper
import config

class context():
    def __init__(self,company_name,company_url,Revenue):
        self.Revenue = Revenue
        self.company_name=company_name
        self.company_url = company_url
        self.azure_config = config.Azure_config()
        self.local_config = config.Local_config()
        self.constant_config = config.Constant_config()
        self.Data={}
        self.CountryGrouping = CountryGrouping.CountryGrouping(self.local_config.GROUPED_DATA_PATH,self.local_config.COUNTRY_DATA_PATH,self.local_config.WEBDRIVER_PATH)
        self.Likedin_obj = linkedin_scraper.format_LinkedIn()
        self.Website_obj = Website_Class.Website()
        self.Glassdoor_obj = Glassdoor.Scraper(self.company_name,self.company_url,self.local_config.WEBDRIVER_PATH)
        self.Model = Heuristic_model.Model(self.local_config.CENSUS_AGE_PATH,self.local_config.CENSUS_INCOME_PATH,self.local_config.CENSUS_POP_PATH)
        self.client = pymongo.MongoClient(self.azure_config.COSMOS_CONNECTION)
        self.mongo_data1 = self.client.get_database(name=self.azure_config.DB_NAME).get_collection(name=self.azure_config.COLLECTION_NAME)


    def Insert_Cosmos(self):
        self.mongo_data1.insert_one(self.Data)
        #mongo_data1.close()

    def check(self):
        #client = pymongo.MongoClient(self.azure_config.COSMOS_CONNECTION)
        #mongo_data1 = client.get_database(name=self.azure_config.DB_NAME).get_collection(name=self.azure_config.COLLECTION_NAME)
        cursor = self.mongo_data1.find({})
        for document in cursor:
            if document['_id'] == self.company_name:
                self.Data = document
        #mongo_data1.close()
        if not self.Data:
            self.Data = self.Scraper()
            self.Insert_Cosmos()

    def Glassdoor_func(self):
        self.Glassdoor_obj.Scrape()
        locations = {}

        if self.Glassdoor_obj.Status == "Location Found":
            c=[]
            for i in self.Glassdoor_obj.locations_data:
                city, country = i.split(", ")
                if len(country) == 2 and us.states.lookup(country) != None:
                    if "us" in list(locations.keys()):
                        locations["us"].append(country)
                    else:
                        locations["us"] = [country]
                else:
                    code = self.CountryGrouping.get_country(country)
                    if code == False:
                        continue 
                    locations[code[1]] = [city]
        return locations

    def Scraper(self):
        Record = {}
        #Record["_id"] = Id
        Record["_id"] = self.company_name
        Record["Compnay_url"] = self.company_url
        Record["Glassdoor"]=self.Glassdoor_func()
        Record["Linkedin"]=self.Likedin_obj.LinkedIn_func(self.local_config.cookie_path, self.company_name,self.company_url)
        Record["Website"]=self.Website_obj.complete_data({'company_url': self.company_url, 'company_name': self.company_name})

        return Record

    def Ditribute(self):
        self.check()
        if 'error' in self.Data['Linkedin'].keys():
            return {"Error":'company not found on linkedin'}
        elif self.Data['Linkedin']['sales_data'] == None:
            return {"Error":'Sales data not available'}

        else:
            Country_Dist,State_Dist = self.Model.Distribute(self.Data['Linkedin']['sales_data'], self.Data['Linkedin']['locations_data'], self.Data['Glassdoor'],self.Data['Website'],self.Revenue)
            return {"Country":Country_Dist,"State":State_Dist}