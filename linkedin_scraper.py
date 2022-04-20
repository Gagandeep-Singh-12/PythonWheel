import time
import json
import re
import datetime
import os
import us
import pickle
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException 
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

import config

#chrome_options.add_argument("--headless") 
#chrome_options.add_argument("--window-size=1920,1080")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--user-agent=Chrome/77")

class LinkedIn():
    
    def __init__(self,cookie_path,company_name, company_website):
        self.company_name = company_name
        self.company_website = company_website
        self.sales_data = None
        self.locations_data = None
        self.headquarter = None
        self.error_dict = {}
        self.error_dict['company_name'] = self.company_name
        self.error_dict['company_website'] = self.company_website
        self.error_dict['data_error1'] = np.nan
        self.error_dict['data_error2'] = np.nan
        self.error_dict['scraper_error'] = np.nan
        self.error_dict['select_section'] = np.nan
        self.restricted = False
        self.authwall = False
        self.cookie_path = cookie_path
        self.linkedin_url = None
        self.local_config = config.Local_config()
        #getting driver
        #if not driver_path:
        #    raise ValueError("Chrome driver Error!!!")
        #elif driver_path:
        #    print("Taking passed chrome driver")
        #    self.driver_path = driver_path
            
        #s = Service(self.driver_path)

        #Intializing chrome Driver
        self.driver = webdriver.Chrome(self.local_config.WEBDRIVER_PATH,options=chrome_options)
        self.driver.maximize_window()
        #self.driver.implicitly_wait(5)
        #self.driver.maximize_window()
        
        
    #main method to get desired results  
    def get_results(self):
        print("company : {}  & company_website : {}".format(self.company_name, self.company_website))
        file = open("logs/scraper_log_cookie_celebal.txt", "a")
        file.write("company : {}  & company_website : {}".format(self.company_name, self.company_website))
        file.write("\n")
        self.load_cookies()
        time.sleep(random.randint(15,25))
        #self.login()
        results = False
        linkedin_link = self.search_company_webiste()
        time.sleep(random.randint(15,25))
        if linkedin_link:
            self.write_content()
            results = self.scraper(linkedin_link)
        else:
            linkedin_link = self.search_google()
            time.sleep(random.randint(15,25))
            #website has been verified and the correspoding content has been written
            if linkedin_link:
                results = self.scraper(linkedin_link)
                
        self.close_drivers()
        
        output = {'company_name': self.company_name,
                  'company_website': self.company_website}
        
        if results:
            output['sales_data'] = self.sales_data
            output['locations_data'] = self.locations_data
        else:
            output['error'] = 'company not found on linkedin'
        output['timestamp'] = datetime.datetime.now()
        return output

###########################           UTILITIES            ##########################

    def load_cookies(self):
        cookie = pickle.load(open(self.cookie_path, "rb"))
        self.driver.get('https://www.linkedin.com/')
        self.driver.add_cookie(cookie)
        self.driver.refresh() 
        try:
            self.linkedin_url=self.driver.current_url 
            print(self.linkedin_url)
        except TimeoutException:
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write("TimeOutException getting current url\n")
            
        file = open("logs/scraper_log_cookie_celebal.txt", "a")
        file.write("linkedinurl after adding cookie -> {}\n".format(self.linkedin_url))
    
    def wait(self, condition, delay):
        return WebDriverWait(self.driver, delay).until(condition)

    def wait_for_element(self, selector, delay=10):
        return self.wait(
            EC.presence_of_element_located((
                By.XPATH, selector)),delay
            )
    def close_drivers(self):
        self.driver.quit()
        
    # Regex method for website filter
    def regex(self,item):
        try:
            m = re.search("(https)?(http)?(://)?(www.)?([A-Za-z_0-9.-]+).*", item)
            #print(m)
            if m:
                #print(item, m.group(5)) 
                return str(m.group(5)).lower()
        except Exception as e:
            print(e)
            
    def select_section(self, driver, section):
        try:
            if driver.linkedin_url == None:
                self.linkedin_url = driver.current_url
                file = open("logs/scraper_log_cookie_celebal.txt", "a")
                file.write("linkedin url in select section -> {}\n".format(self.linkedin_url))

            if driver.current_url.find('authwall?') != -1:
                self.authwall = True
                file = open("logs/scraper_log_cookie_celebal.txt", "a")
                file.wrie("authwall = True\n")
                self.close_drivers()
            
            
            self.wait_for_element("//ul[@class='org-page-navigation__items ']/li/a")
            time.sleep(10)
            ##Random 
            time.sleep(random.randint(15,25))
            ##
            org_page_navigation_items = self.driver.find_elements(By.XPATH, "//ul[@class='org-page-navigation__items ']/li/a")
            #locate hyperlinks to required Section
            sections = [my_elem.get_attribute('href') for my_elem in org_page_navigation_items]
            link = [sec for sec in sections if sec.split('/')[-2] == section][0]
            ##Random 
            time.sleep(random.randint(15,25))
            ##
            driver.get(link)
            ##vhecking for wether linkedin has restricted your account
            if section == 'people':
                checking = self.check_for_restriction()
                if checking:
                    self.restricted = True
                    file = open("logs/scraper_log_cookie_celebal.txt", "a")
                    file.write('Restricted')

            ##
         
        except TimeoutException as e:
            #print(e)
            print("select section error for section {}".format(section))
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write("select section error for section {}".format(section))
            file.write("\n")
            self.error_dict['select_section'] = "select section error for section {}".format(section)
            pass

    def check_for_restriction(self):
        try:
            self.wait_for_element('//p')
            time.sleep(4)
            p_elems = self.driver.find_elements(By.XPATH, '//p')
            check = 'The filters applied did not return any results. Try clearing some filters and try again.'
            if check in [e.text for e in p_elems] :
                return True
            return False 
        except:
            return False

    ##this will write locations content and when this function is called, driver is at the about section
    def write_content(self):
    
        about_source = self.driver.page_source
        global linkedin_soup
        linkedin_soup = BeautifulSoup(about_source.encode("utf-8"), "html")
        content = linkedin_soup.prettify()
        with open('content.txt', 'w') as f:
            f.write(content)
            
        with open('content.txt') as f1:
            for line in f1.readlines():
                if (line.find("confirmedLocations")!=-1):
                    #print("Y")
                    with open('locations_content.txt','w') as lc:
                        lc.write(line)
                    break
                
    def find_locations(self, content):
   
        with open(content, 'r') as f:
            d = f.read()
        res = json.loads(d)
        #locations => keys-country, values = city
        locations = {}
        headquarter_loc = {}
        
        for item in res['included']:
            if 'confirmedLocations' in item.keys():
                #print(len(item['confirmedLocations']))
                for loc_dict in item['confirmedLocations']:      
                    try:
                        if loc_dict['city']:
                            city = loc_dict['city']
                    except:
                        city = np.NaN
                        
                    if loc_dict['headquarter']:
                        headquarter_loc['country'] = loc_dict['country']
                        headquarter_loc['city'] = city
                    #data about locations where headquarter = false        
                    if loc_dict['country'] in locations.keys():
        
                        locations[loc_dict['country']].append(city)
                    else:
                        locations[loc_dict['country']] = []
                        locations[loc_dict['country']].append(city)
                break
            
        if len(locations) == 0:
            self.error_dict['locations'] = True
            
        return locations, headquarter_loc 
    
    def find_locations2(self,content):
   
        with open(content, 'r') as f:
            d = f.read()
        res = json.loads(d)
        #locations => keys-country, values = city
        locations = {}
        headquarter_loc = {}
        
        for item in res['included']:
            if 'confirmedLocations' in item.keys():
                #print(item['confirmedLocations'])
                #print(len(item['confirmedLocations']))
                for loc_dict in item['confirmedLocations']:      
                    try:
                        if loc_dict['city']:
                            city = loc_dict['city']
                    except:
                        city = np.NaN
                        
                    if loc_dict['headquarter']:
                        headquarter_loc['country'] = loc_dict['country']
                        headquarter_loc['city'] = city
                    #data about locations where headquarter = false        
                    if loc_dict['country'] in locations.keys():
        
                        locations[loc_dict['country']].append(city)
                    else:
                        locations[loc_dict['country']] = []
                        locations[loc_dict['country']].append(city)
                break
        #'locations not found in included key'   
        if len(locations) == 0:
            self.error_dict['data_error1'] = True
        #when data is in data key though leading to discrpancy
        try:
            
            if len(locations) == 0:
                for loc_dict in res['data']['confirmedLocations']:
                    try:
                        if loc_dict['city']:
                            city = loc_dict['city']
                    except:
                        city = np.nan
                    if loc_dict['headquarter']:
                        headquarter_loc['country'] = loc_dict['country']
                        headquarter_loc['city'] = loc_dict['city']
                    if loc_dict['country'] in locations.keys():
                            locations[loc_dict['country']].append(city)
                    else:
                        locations[loc_dict['country']] = []
                        locations[loc_dict['country']].append(city)
        except:
            #print('finding locations in data key')
            self.error_dict['data_error2'] = True
             
        return locations, headquarter_loc
    
    def get_sales_data(self):
        try:
            self.select_section(self.driver, 'people')

            ##Random 
            time.sleep(random.randint(15,25))
            ##
            #click next button
            self.wait_for_element('//button[@aria-label="Next"]').click()
            time.sleep(random.randint(15,25))
            self.wait_for_element('//div[@class="insight-container"]//h4[text()="What they do"]')
            
            #caculation for applying sales filter
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            res = soup.find_all('h4')
            for i in res:
                if i.text.strip() == 'What they do':
                    buttons1 = i.findParent('div').find_next_siblings('button')
                    id = i.findParent('div').parent.parent.attrs['id']
            
            #which button is for sales?
            c = 1
            for i in buttons1:
                span = i.find('span')
                if span.text == 'Sales':
                    #print(span.find_parent('button'))
                    #print(c)
                    break
                c += 1
                
            sales_filter = '//*[@id="{}"]/div/button[{}]'.format(id,c)
            ##Random 
            time.sleep(random.randint(15,25))
            ##
            #click show more if present
            try:
                time.sleep(random.randint(15,25))
                self.wait_for_element('//*[@id="main"]/div[2]/div/div[1]/div[2]/button').click()
            except:
                pass
            
            try:
                time.sleep(random.randint(15,25))
                WebDriverWait(self.driver, 25).until(
                    EC.element_to_be_clickable((By.XPATH,sales_filter))
                ).click()
            except Exception as e:
                print('Time out at sales filter')
                file = open("logs/scraper_log_cookie_celebal.txt", "a")
                file.write('Time out at sales filter\n')
                pass
                #print('Time out at sales filter')
                #self.error_dict['get_sales_data1']= 'Time out at sales filter'
                #print(e)
            time.sleep(random.randint(15,25))
            self.wait_for_element('//div[@class="artdeco-card p4 m2 org-people-bar-graph-module__geo-region"]//button/div/strong')
            #get employee counts
            time.sleep(random.randint(15,25))
            emp_counts =self.driver.find_elements(By.XPATH, '//div[@class="artdeco-card p4 m2 org-people-bar-graph-module__geo-region"]//button/div/strong')
            time.sleep(random.randint(15,25))
            emp_counts = [elem.text for elem in emp_counts]  
            #get country names
            country_names = self.driver.find_elements(By.XPATH, '//div[@class="artdeco-card p4 m2 org-people-bar-graph-module__geo-region"]//button/div/span')
            time.sleep(random.randint(15,25))
            country_names = [country.text for country in country_names]
            
            sales_dic = {"country":country_names, "sales_count":emp_counts}
            return sales_dic
        
        #there are no members belonging to sales
        except Exception as e:
            print('exception inside get_sales_data_func')
            #print(e)
            #self.error_dict['get_sales_data2'] = 'inside get_sales_data_func'
            #print(e)
            return None
        
    def search_google(self):
        try:
            google_search_url = "https://www.google.com/search?q="+self.company_name+"+linkedin"
            time.sleep(random.randint(15,25))
            self.driver.get(google_search_url)
            time.sleep(random.randint(15,25))
            self.wait_for_element("//div[@id='search']")
            time.sleep(random.randint(15,25))
            linkedin_URLS = [my_elem.get_attribute("href") for my_elem in self.driver.find_elements(By.XPATH,"//div[@class='yuRUbf']/a")]
            #ensuring all links contain linkedin
            time.sleep(random.randint(15,25))
            linkedin_URLS = [link for link in linkedin_URLS if link.find('linkedin')!= -1 and link.find('company')!=-1]
            #print(linkedin_URLS)
            
            #eg. obj3 = LinkedIn(cookie, 'AppYea, Inc.', 'https://www.sleepxclear.com/')
            if len(linkedin_URLS) == 0:
                #print('YYYYY')
                m = re.search("(https)?(http)?(://)?(www.)?([A-Za-z_0-9-]+).*", self.company_website)
                search = m.group(5)
                time.sleep(random.randint(15,25))
                google_search_url = "https://www.google.com/search?q="+search+"+linkedin"
                time.sleep(random.randint(15,25))
                self.driver.get(google_search_url)
                time.sleep(random.randint(15,25))
                self.wait_for_element("//div[@id='search']")
                linkedin_URLS = [my_elem.get_attribute("href") for my_elem in self.driver.find_elements(By.XPATH,"//div[@class='yuRUbf']/a")]
                #ensuring all links contain linkedin
                time.sleep(random.randint(15,25))
                linkedin_URLS = [link for link in linkedin_URLS if link.find('linkedin')!= -1 and link.find('company')!=-1]
                #print(linkedin_URLS)
                            
            #verification
            for link_suggestion in linkedin_URLS:
                time.sleep(random.randint(15,25))
                if self.verify_website(link_suggestion):
                    return self.driver.current_url
            return False
                
        except Exception as e:
            #print('Error in google search')
            #print(e)
            return False       
        
    def verify_website(self, link):
        try:
            if ~(link.startswith('https://www.linkedin.com/company')):
                link = "https://www.linkedin.com/company"+link.split("company")[-1] 
                print(link)
            time.sleep(random.randint(15,25))
            self.driver.get(link)
            ##Random 
            time.sleep(random.randint(15,25))
            ##
            self.select_section(self.driver, 'about')
            self.wait_for_element('//section[@class="artdeco-card p5 mb4"]')
            self.write_content()
            
            for h in linkedin_soup.find_all('dt'):   
                if h.text.strip().lower() == 'website':
                    #print("y")
                    website = h.findNextSibling().find('a').attrs['href']
                    print("Website Checking : {} & {}".format(website,self.company_website))
                    web1 = self.regex(website)
                    web2 = self.regex(self.company_website)
                    print('web1 : {} & web2 : {}'.format(web1,web2))
                    
                    #if website is verified then we will collect required data
                    if web1 == web2:
                        #print('match')
                        return True
                    #case = where website mentioned in linkedin doesn't match with given company website
                    #but if we visit it, there is a match 
                    #eg.=>company_website=https://4sight.cloud/about & linkedin = http://www.4sightholdings.com
                    else:
                        self.driver2 = webdriver.Chrome(self.local_config.WEBDRIVER_PATH,options=chrome_options)
                        time.sleep(random.randint(15,25))
                        self.driver2.get(website)
                        time.sleep(random.randint(15,25))
                        website = self.driver2.current_url
                        time.sleep(random.randint(15,25))
                        self.driver2.close()
                        web1 = self.regex(website)
                        web2 = self.regex(self.company_website)
                        print('web1 : {} & web2 : {}'.format(web1,web2))
                        if web1 == web2:
                            return True
        
            return False
        #for case when we open a link of the employee belonging to a company
        except:
            return False     
    
    #if we find linked_link driver will open it &this func returns that linkedin link
    #here we don't need to verify the website
    def search_company_webiste(self):
        try:
            self.driver.get(self.company_website)
            time.sleep(random.randint(15,25))
            self.wait_for_element('//a')
            time.sleep(random.randint(15,25))
            links = [elem.get_attribute('href') for elem in self.driver.find_elements(By.XPATH, '//a')]
            
            #checking if link is in area tag (eg. 'https://www.01com.com/')
            try:
                area_links = self.driver.find_elements(By.XPATH, '//map/area[@href]')
                time.sleep(random.randint(15,25))
                links.extend([elem.get_attribute('href') for elem in area_links])
                time.sleep(random.randint(15,25))
            except:
                pass
            
            #checking for linkedin link
            for link in links:
                if link.find('https://www.linkedin.com/company') != -1:
                    time.sleep(random.randint(15,25))
                    self.driver.get(link)
                    time.sleep(random.randint(15,25))
                    self.select_section(self.driver, 'about')
                    time.sleep(random.randint(15,25))
                    return self.driver.current_url
            return False
            
        except Exception as e:
            #print(e)
            return False

    #scraper will assume that write_content() has already been called on 'About' section
    def scraper(self, company_link):
        try:
            #getting locations data
            locations, headquarter_loc  = self.find_locations2('locations_content.txt')
            self.locations_data = locations
            self.headquarter = headquarter_loc
            ##Random 
            time.sleep(random.randint(15,25))
            ##
            sales_dic = self.get_sales_data() 
            self.sales_data = sales_dic
            #if everything is scraped fine
            return True
            
        except Exception as e:
            print("ERROR : ",e)
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write("Error inside scarper\n")
            print('error inside scraper')
            self.error_dict['scraper_error'] = True

import CountryGrouping
class format_LinkedIn():

    def __init__(self):
        self.local_config = config.Local_config()
        self.country_object = CountryGrouping.CountryGrouping(self.local_config.GROUPED_DATA_PATH,self.local_config.COUNTRY_DATA_PATH,self.local_config.WEBDRIVER_PATH)
        self.LinkedIn_email = 'johnsinha183@gmail.com'
        self.LinkedIn_password = 'mypassword123'
  
    def update_cookies(self):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))  
        display.start()
        driver = webdriver.Chrome(self.local_config.WEBDRIVER_PATH,options=chrome_options)
        #login
        driver.get('https://www.linkedin.com/login')
        time.sleep(8)
        username = driver.find_element(By.ID, 'username')
        username.send_keys(self.LinkedIn_email)
        time.sleep(8)
        pass_word= driver.find_element(By.ID, 'password')
        pass_word.send_keys(self.LinkedIn_password)
        time.sleep(8)
        pass_word.submit()
        with open('logs/update_cookie.txt','a') as f:
            f.write('Password & Id submitted\n')
        #save cookies
        print("saving cookie")
        with open('logs/update_cookie.txt','a') as f:
            f.write('Saving cookies\n')
        time.sleep(10)
        cookies=driver.get_cookies()
        print(cookies)
        for cookie in cookies:
            if(cookie['name']=='li_at'):
                #cookie['domain']='www.linkedin.com'
                x={
                'name': 'li_at',
                'value': cookie['value'],
                'domain': 'www.linkedin.com'
                }
                break

        '/home/celebal/Data/cookies'
        pickle.dump(x , open("/home/celebal/Data/cookies/updated_cookies_activity.pkl","wb"))
        with open('logs/update_cookie.txt','a') as f:
            f.write('Cookies saved\n')
        driver.close() 
        display.stop()


    def get_data_from_linkedin(self,cookie_path,company_name, company_website):
        
        file = open("logs/scraper_log_cookie_celebal.txt", "a")
        file.write('current cookie : {}\n'.format(cookie_path))
        
        obj=LinkedIn(cookie_path,company_name, company_website) 
        output_ = obj.get_results()

        if self.linkedin_url.main_driver.current_url.startswith("https://www.linkedin.com/signup"):
            file = open('logs/update_cookie.txt','a')
            file.write('company_name : {}  &  company_url {}\n'.format(company_name, company_website))
            try:
                self.update_cookies()
                file.write('cookies updated\n')
                obj=LinkedIn(cookie_path,company_name, company_website) 
                output_ = obj.get_results()
            except Exception as e:
                file.write('Exception occured while updating cookie i.e. {}'.format(e))
            file.close()
        
        if obj.authwall:
            print('##########AUTHWALL#############################')
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write('##########AUTHWALL#############################\n')
            
        if obj.restricted:
            print("!!!!!!!!!!!!!!!!!!!!RESTRICTED!!!!!!!!!!!!!!!!")
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write("!!!!!!!!!!!!!!!!!!!!RESTRICTED!!!!!!!!!!!!!!!!\n")

            
        if obj.linkedin_url.find('checkpoint') != -1 :
            print("##########Checkpoint##############")
            file = open("logs/scraper_log_cookie_celebal.txt", "a")
            file.write("##########Checkpoint##############\n")
            

        ##to ensure same file is not being used
        if 'error' not in output_.keys():
            try:
                os.remove('content.txt')
                os.remove('locations_content.txt')
            except Exception as e:
                print('File!!!!!!!!!!!')
                print(e)

        return output_, obj.error_dict

    def format_linkedin_data(self,c):
        '''c -> data for one company '''
        #print('\n\n',i)
        d = {}#for each company
        e = {}#error for each company
        #d['company_name'], d['company_website'] = c['company_name'], c['company_website']
        e['company_name'], e['company_website'] = c['company_name'], c['company_website']
        ##logic
        if 'locations_data' in c.keys():
            if c['locations_data'] != {}:
                #print(c['locations_data'])
                formatted_location_data = {}
                #looping through each countr; k->country & v -> [locations]
                for k,v in c['locations_data'].items():
                    #print(k)
                    new_v = list(pd.Series(v).dropna().values)
                   
                    #if len(new_v) <len(v):
                    #    print('v ---> ', v)
                    #    print('new_v ----> ',new_v)
                    #if new_v is empty then skip that key,value pair
                    if len(new_v) == 0:
                        #print('YES || i {} '.format(i))
                        continue

                     #1
                    new_v = [loc.strip() for loc in new_v]
                        
                    if len(k) == 2 and self.country_object.get_country_from_code(k.lower()) and k != 'OO':
                        #print('k -> ',k)
                        formatted_location_data[k.lower()] = new_v
                    else:
                        res = self.country_object.get_country(k.lower())#pointer
                        #print('eeeee    : {}'.format(k))
                        if res != False:
                            country = res[1]
                            formatted_location_data[country] = new_v
                        else:
                            #print(i)
                            if 'false' in e.keys():
                                e['false'].append(k)
                            else:
                                e['false'] = []
                                e['false'].append(k)

                d['locations_data'] = formatted_location_data
            else:
                d['locations_data'] = c['locations_data']
                #print(c)
        else:
            #'company not found on linkedin' we will know no location data is there
            #d['locations_data'] = c['error']
            pass
            #print('\nNN')
            #print(c,'\n')
        #print('\n')
        #print(c,'\n\n')
        if 'error' not in c.keys():
            c['locations_data'] = d['locations_data']
            
            #print(c['locations_data'],'\n')
            for k,v in c['locations_data'].items():
                if k == 'us':
                    #print(v)
                    #print(c['locations_data'][k])
                    abbr_v_us = []
                    for i in v:
                        if re.search(r"[a-zA-Z\ ]+", i) != None:
                            try:
                                new_i = us.states.lookup(self.country_object.geoloc_for_state(i)).abbr 
                            except :
                                #print('ecx')
                                new_i = us.states.lookup(self.country_object.geoloc_for_state(i + ',US')).abbr 
                            abbr_v_us.append(new_i)
                    #print(abbr_v_us)
                    c['locations_data'][k] = abbr_v_us
                    #print(c['locations_data'][k])
        
        if 'error' not in c.keys() and c['sales_data'] != None:
            country_abbr = []
            for cn in c['sales_data']['country']:
                if cn != "Other":
                    try:
                        result = self.country_object.get_country(cn)
                        if result ==False:
                            cn1 = re.sub("area","",cn).strip()
                            cn1 = re.sub("Area","",cn1).strip()
                            result = self.country_object.get_country(cn1)
                            if result != False:
                                country_abbr.append(result[1])
                            else:
                                print('error')
                                file = open("logs/scraper_log_cookie_celebal.txt", "a")
                                file.write("country abbreviation error\n")
                        else:
                            country_abbr.append(result[1])
                    except:
                        country_abbr.append('NA')
                else:
                    country_abbr.append('Other')
            c['sales_data']['country'] = country_abbr
                    
        return c,e
    ##function to get formatted, clean data from LinkedIn
    def LinkedIn_func(self,cookie_path,company_name, company_website):
        output_, err = self.get_data_from_linkedin(cookie_path,company_name, company_website)
        c, e = self.format_linkedin_data(output_)
        return c
