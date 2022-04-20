import config
import pandas as pd
import re
import us
import os
import time
import random
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless") 

class scrape_us():
    def __init__(self):
        self.local_config = config.Local_config()
        self.driver_path = self.local_config.WEBDRIVER_PATH 
        self.driver = webdriver.Chrome(self.driver_path,options=chrome_options)
        self.driver.maximize_window()
        self.file = open('logs_us_census.txt', 'a')
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        self.file.write('\nDate time  : {} .\n'.format(dt_string))
    
    def get_us_data(self):
        
        try:
            link = 'https://www.census.gov/programs-surveys/acs/news/data-releases.html'
            self.driver.get(link)
            time.sleep(5)
            date_ = date.today()
            year = date_.strftime('%Y')
            
            for i in range(10):
                res_data = self.get_latest_data(year)
                if len(res_data) == 0:
                    year = str( int(year) - 1)
                    print(year)
                else:
                    print(res_data[0])
                    break
                
            if len(res_data[0]) == 0:
                print('Could not find data for latest year')
                self.file.write('Could not find data for latest year.\n')
                
            self.driver.get(res_data[0])
            time.sleep(random.randint(2,8))
            data_link = [e.get_attribute('href') for e in self.driver.find_elements(By.XPATH,'//a') if 'American Community Survey Experimental Data' in e.text.split('\n')]
            if len(data_link) != 0:  
                time.sleep(random.randint(2,8)) 
                self.driver.get(data_link[0])
            else:
                print('log-> data_link error')
                self.file.write('data_link error.\n')
                
            filter = year + ' ACS 1-Year Experimental Data Tables' 
            data_link2 = [e.get_attribute('href') for e in self.driver.find_elements(By.XPATH, '//a') if filter in e.text.split('\n')]
            if len(data_link2) != 0:
                time.sleep(random.randint(2,8))
                self.driver.get(data_link2[0])
            else:
                print('log -> data_link2 error')
                self.file.write('data_link2 error.\n')
            
            economic_button = [e for e in self.driver.find_elements(By.XPATH, '//button') if e.text == 'Economic']
            if len(economic_button) != 0:
                time.sleep(random.randint(2,8))
                economic_button[0].click()
            else:
                print('log-> economic button')
                self.file.write('economic button error.\n')
            time.sleep(3)
            
            self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            #set download path (set to current working directory in this example)
            params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow','downloadPath':os.getcwd()}}
            time.sleep(random.randint(2,8))
            command_result = self.driver.execute("send_command", params)
            
            median_income = [e for e in  self.driver.find_elements(By.XPATH, '//a') if e.text.find('Median Household Income')!= -1]
            if len(median_income) != 0:
                time.sleep(random.randint(2,8))
                median_income[0].click()
            else:
                print('log-> median_income error')
                self.file.write('median_income error.\n')
            
            time.sleep(10)
            
            files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
            os.rename(files[-1], 'median_household_income.xlsx')
            
            demographic_button = [e for e in self.driver.find_elements(By.XPATH, '//button') if e.text == 'Demographic']
            if len(demographic_button)!=0:
                time.sleep(random.randint(2,8))
                demographic_button[0].click()
            else:
                print('log -> demographic button error.')
                self.file.write('demographic button error.\n')
            
            median_age = [e for e in  self.driver.find_elements(By.XPATH, '//a') if e.text.find('Median Age by Sex')!= -1]
            if len(median_age)!=0:
                time.sleep(random.randint(2,8))
                median_age[0].click()
                time.sleep(8)
            else:
                print('log-> median age error.')
                self.file.write('median age error.\n')
                
            files = sorted(os.listdir(os.getcwd() ), key=os.path.getmtime)
            os.rename(files[-1], 'median_age_by_sex.xlsx')
            
            population = [e for e in  self.driver.find_elements(By.XPATH, '//a') if e.text.find('Population by Sex')!= -1]
            if len(population) != 0:
                time.sleep(random.randint(2,8))
                population[0].click()
                time.sleep(8)
            else:
                print('log-> population error.')
                self.file.write('population error.\n')
            
            files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
            os.rename(files[-1], 'population_by_sex.xlsx')
            
            source = os.getcwd() + '/'
            #destination = os.getcwd() + '/census_data/'
            destination = '/home/celebal/Data/census_data/US/'
            files = ['median_age_by_sex.xlsx', 'median_household_income.xlsx','population_by_sex.xlsx']
            for f in files:
                os.rename(source + f, destination + f)
        except Exception as e:
            print(e)
            self.file.write('Ecxeption = {}.\n'.format(e))
            

    def get_latest_data(self,year):
        return [e.get_attribute('href') for e in self.driver.find_elements(By.XPATH, '//a') if e.get_attribute('text').strip() == year]
     


class clean_data():
    def __init__(self):
        self.cols = [i for i in range(1, 104) if i%2 !=0]

    def clean_median_household_income(self):
        data = pd.read_excel('/home/celebal/Data/census_data/US/median_household_income.xlsx')
        req_data = data.iloc[5:8]
        req_data = req_data.iloc[:, self.cols]
        new_header = req_data.iloc[0] #grab the first row for the header
        req_data = req_data[1:] #take the data less the header row
        req_data.columns = new_header #set the header row as the df header
        req_data.drop(columns=['United States'], inplace = True)
        median_hosehold_income = pd.DataFrame(req_data.loc[7, :])
        abbreviations = []
        for st in median_hosehold_income.index:
            #print(state)
            state = us.states.lookup(st)
            abbreviations.append(state.abbr)
        median_hosehold_income.index = abbreviations
        m1 = median_hosehold_income[7].apply(lambda x: int(re.sub(',', '', x)))
        pd.DataFrame(m1).reset_index().rename(columns = {'index':'state_code', 7 : 'median_income'}).to_csv('/home/celebal/Data/census_data/US/clean_data/median_income.csv')
    
    def clean_meadian_age(self):
        df = pd.read_excel('/home/celebal/Data/census_data/US/median_age_by_sex.xlsx')
        req_data = df.iloc[5:11]
        req_data = req_data.iloc[:,self.cols]
        new_header = req_data.iloc[0]
        req_data = req_data[1:]
        req_data.columns = new_header 
        req_data = req_data.loc[8]
        req_data.drop(index = ['United States'], inplace = True)
        abbreviations = []
        for st in req_data.index:
            #print(state)
            state = us.states.lookup(st)
            abbreviations.append(state.abbr)
        req_data.index = abbreviations
        req_data =req_data.astype('float32')
        pd.DataFrame(req_data).reset_index().rename(columns={'index':'state_code', 8:'median_age'}).to_csv('/home/celebal/Data/census_data/US/clean_data/median_age.csv')


    def clean_population(self):
        df = pd.read_excel('/home/celebal/Data/census_data/US/population_by_sex.xlsx')
        req_data= df.iloc[5:8,:]
        req_data = req_data.iloc[:,self.cols]
        new_header = req_data.iloc[0] 
        req_data = req_data[1:] 
        req_data.columns = new_header 
        req_data = req_data.loc[7]
        req_data.drop(index = ['United States'], inplace = True)
        abbreviations = []
        for st in req_data.index:
            #print(st)
            state = us.states.lookup(st)
            abbreviations.append(state.abbr)
        req_data.index = abbreviations
        req_data = req_data.apply(lambda x : re.sub(',', '', x)).astype('int')
        pd.DataFrame(req_data).reset_index().rename(columns = {'index':'state_code', 7:'population'}).to_csv('/home/celebal/Data/census_data/US/clean_data/population.csv')
    
    def clean_data(self):
        self.clean_median_household_income()
        self.clean_meadian_age()
        self.clean_population()