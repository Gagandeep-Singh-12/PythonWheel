
class Local_config():
    def __init__(self):
        self.GROUPED_DATA_PATH = '/home/celebal/Data/grouped_countries1.pkl'
        self.WEBDRIVER_PATH = '/home/azureuser/.wdm/drivers/chromedriver/linux64/100.0.4896.60/chromedriver'
        self.COUNTRY_DATA_PATH="/home/celebal/Data/final.csv"
        self.CENSUS_AGE_PATH="/home/celebal/Data/census_data/US/clean_data/median_age.csv"
        self.CENSUS_INCOME_PATH="/home/celebal/Data/census_data/US/clean_data/median_income.csv"
        self.CENSUS_POP_PATH="/home/celebal/Data/census_data/US/clean_data/population.csv"
        self.cookie_path = '/home/celebal/Data/cookies/cookies_activity.pkl'
        self.revenue_file_path = '/home/celebal/Pipeline/util_files/revenue.json'
        #self.revenue_file_pointer = open(self.revenue_file_path, 'r+')

class Constant_config():
    def __init__(self):
        # Threshold for fuzzy logic
        self.Threshold = 90
        # Keywords to obtain relevant pages to be scraped from company website
        self.Keywords = ['locations','contact-us','company','home','about'] 
        self.WINDOW_SIZE = "1920,1080"
class Azure_config():
    def __init__(self):
        self.COSMOS_CONNECTION = "mongodb://celebal:bZPUhXkQDcdWioAIiwECCdSEiZL3zmQ6bojzYjdiDxQlHhBgzKrJjiuYCWtEbSB4QcinajhByNwKbWlsRoBQ0A==@celebal.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@celebal@"
        self.DB_NAME = "geography_sizing"
        self.COLLECTION_NAME = "company_data"