#import
from selenium import webdriver
from selenium.webdriver.common.by import By
#import time
#from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException 
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
#import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import re
from pyvirtualdisplay import Display

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--user-agent=Chrome/77")

class Scraper():
    def __init__(self,company_name,company_website,driverpath):
        self.company_name = company_name
        self.company_website = company_website
        self.locations_data = []
        self.Status = "Location Found"
        self.glassdoor_website_url = ''
        self.chrome_options =chrome_options
        self.driverpath = driverpath

        # Starting Display for 
        #self.display = Display(visible=0, size=(1920, 1080))  
        #self.display.start()

        #Intializing chrome Driver
        self.driver = webdriver.Chrome(self.driverpath,options=self.chrome_options)
        self.driver.maximize_window()

        try:
            self.driver.get('https://www.glassdoor.co.in/member/home/index.htm')
        except TimeoutException:
            self.Status = "Timed Out while loading Glassdoor"

    
    def wait(self,condition, delay=10):
        #print("This is web",WebDriverWait(self.driver, self.timeout).until(condition))
        return WebDriverWait(self.driver, delay).until(condition)

    def wait_for_element(self,selector, delay=10):
        return self.wait(
            EC.presence_of_element_located((By.XPATH, selector)),delay)

    def wait_for_element_ID(self,selector, delay=10):
        return self.wait(
            EC.presence_of_element_located((By.ID, selector)),delay)

    def login(self):
        self.wait_for_element('//*[@id="inlineUserEmail"]')
        email = self.driver.find_element(By.XPATH, '//*[@id="inlineUserEmail"]')
        email.send_keys('josephrobertson608@gmail.com')
        self.wait_for_element('//*[@id="inlineUserPassword"]')
        password = self.driver.find_element(By.XPATH, '//*[@id="inlineUserPassword"]')
        password.send_keys("Gn@zZJ5R")
        self.wait_for_element('//button[@name="submit"]')
        self.driver.find_element(By.XPATH, '//button[@name="submit"]').click()

    def Select_Dropdown(self):
        selected_term = [elem.text for elem in self.driver.find_elements(By.CLASS_NAME, "selectedLabel")][0]
        target_text = "Companies"
        if selected_term != target_text:

            dropdown_element = self.wait_for_element('//*[@id="scBar"]/div/div[2]/div',30)
            dropdown_element.click()

            xp = '//*[@id="scBar"]/div/div[2]/div/div[2]/div/ul/li/span[text()="{}"]'.format(target_text)
            target_element =WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH,xp)))
            target_element.click()
    
    def regex(self,item):
        #try:
        m = re.search("(https)?(http)?(://)?(www.)?([A-Za-z_0-9.-]+).*", item)
        #print(m)
        if m:
            #print(item, m.group(5)) 
            return str(m.group(5)).lower()
        #except Exception as e:
        #    print(e)

    def Verify(self):
        glassdoor_web = self.regex(str(self.glassdoor_website_url))
        web2 = self.regex(str(self.company_website))
        #print("{} - {} - {}".format(glassdoor_web,web2,fuzz.ratio(glassdoor_web,web2)))
        if glassdoor_web == web2:
            return True
        else: 
            d1 = webdriver.Chrome('/home/celebal/.wdm/drivers/chromedriver/linux64/99.0.4844.51/chromedriver',options=self.chrome_options)
            d2 = webdriver.Chrome('/home/celebal/.wdm/drivers/chromedriver/linux64/99.0.4844.51/chromedriver',options=self.chrome_options)
            try:
                #d1.get(self.company_website)
                d2.get(self.glassdoor_website_url)
                print(str(d2.current_url))
                w1 = self.regex(str(self.company_website))
                w2 = self.regex(str(d2.current_url))
                d1.quit()
                d2.quit()
                if w1 == w2:
                    return True
                else:
                    return False
            except:
                d1.quit()
                d2.quit()
                return False
    
    def Search_Company(self):
        try:
            self.wait_for_element_ID('sc.keyword',30)
        except Exception as e:
            print(self.driver.current_url)
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+str(e)+"," +self.driver.current_url)
            file.close()
        
        
        self.driver.find_element(By.ID, 'sc.keyword').send_keys(self.company_name)
        
        self.Select_Dropdown()
        
        search = self.wait_for_element_ID('sc.location')
        
        while self.driver.find_element(By.XPATH, '//*[@id="sc.location"]').get_attribute('value') != '':
            search.send_keys(Keys.BACK_SPACE)
            
        #Hit Search button
        search_button = self.wait_for_element('//*[@id="scBar"]/div/button',45)
        try:
            search_button.click()
        except Exception as e:
            print(self.driver.current_url)
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+str(e)+"," +self.driver.current_url,"  search button  ")
            file.close()  

    def get_Company_website(self):
        #if "Overview" not in self.driver.current_url:
            
        #else:
        li_elements = self.driver.find_elements(By.XPATH,"//a[@class='css-1hg9omi css-1cnqmgc']")
        if len(li_elements) == 0:
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+"No lInks"+"," +self.driver.current_url)
            file.close()
            print("No links")
        else:
            self.glassdoor_website_url=li_elements[0].text

    
    def Get_loc(self):
        try:
            self.wait_for_element("//a[@class = 'moreBar']")
            self.driver.find_element(By.XPATH,"//a[@class = 'moreBar']").click()
        except TimeoutException:
            self.Status = "Locations Not Found"
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+"Loc not found"+"," +self.driver.current_url)
            file.close()
            return -1

        #driver.current_url
        try:
            self.wait_for_element("//p[@class='mb-0 mt-0 d-flex align-items-center']//a")
        except TimeoutException:
            self.Status = "Locations Not Found"
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+"Loc not found"+"," +self.driver.current_url)
            file.close()
            return -1
        for i in self.driver.find_elements(By.XPATH,"//p[@class='mb-0 mt-0 d-flex align-items-center']//a"):
                self.locations_data.append(i.text)

    
    def Scrape(self):
        self.login()
        try:    
            self.Search_Company()
        except Exception as e:
            #print(self.driver.current_url)
            file = open("logs/glassdoor_log.txt","a")
            file.write("\n"+self.company_name+", "+str(e)+"," +self.driver.current_url+", Seacrch company ")
            file.close()
            return -1
        
        if "Overview" not in self.driver.current_url:
            try:
                self.wait_for_element('//div[@class = "single-company-result module "]//div[@class="col-9 pr-0"]//h2//a')
                self.wait_for_element('//div[@class = "single-company-result module "]//span//a')
            except TimeoutException:
                self.Status = "Comapny Not found"
                self.driver.quit()
                file = open("logs/glassdoor_log.txt","a")
                file.write("\n"+self.company_name+", "+"Comapny Not found")
                file.close()
                #self.display.stop()
                return -1
            href = self.driver.find_elements(By.XPATH,'//div[@class = "single-company-result module "]//div[@class="col-9 pr-0"]//h2//a')
            comapny_web = self.driver.find_elements(By.XPATH,'//div[@class = "single-company-result module "]//span//a')
            if len(comapny_web)!=0:
                for i, j in zip(href,comapny_web):
                    self.glassdoor_website_url = j.text
                    if self.Verify():
                        i.click()
                        self.Get_loc()
                        break                            
                    else:
                        self.Status = "No Company Verified"
            else:
                self.Status = "Comapny Not found"
        else:
            self.get_Company_website()        
            if self.Verify():
                self.Get_loc()
            else:
                self.Status = "Not Verified"
        
        self.driver.quit()
        #self.display.stop()
