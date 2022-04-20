
import pickle
from pyvirtualdisplay import Display
 #import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.common.keys import Keys
import re
from geopy.geocoders import Nominatim
import geocoder
import pandas as pd


class CountryGrouping():
    def __init__(self,grouped_countries_path,countries_code_path,driver_path):
        self.driver_path = driver_path
        self.grouped_countries = pickle.load(open(grouped_countries_path, 'rb'))
        self.countries_code_path = countries_code_path
        self.locator = Nominatim(user_agent='geoapiExercises')

    def find_grouped_countries(self,linkedin_location):
        for k,v in self.grouped_countries.items():
            if linkedin_location in v:
                return k
        return False

    def get_gecoder(self,linkedin_location):
        g = geocoder.arcgis(linkedin_location)
        if g.status == 'OK':
            return g.lat, g.lng
        else:
            return 'error in geocoder'

    def geoloc(self,linkedin_location):
        res2 = self.get_gecoder(linkedin_location)
        if res2 == 'error in geocoder':
            return False
        else:
            Latitude , Longitude = res2[0], res2[1]
            location = self.locator.reverse(str(Latitude)+","+str(Longitude))
            address = location.raw['address']
            return address.get('country', '')

    def wait(self,condition, delay,driver):
        #print("This is web",WebDriverWait(self.driver, self.timeout).until(condition))
        return WebDriverWait(driver, delay).until(condition)

    def wait_for_element(self,selector,driver, delay=10):
        return self.wait(
            EC.presence_of_element_located((
                By.XPATH, selector)),delay,driver
            )

    def iso_browser(self,linkedin_location):
        display = Display(visible=0, size=(800, 800))  
        #display.start()
        chrome_options = Options()
        # maximized window
        chrome_options.add_argument("--start-maximized")
        #chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(self.driver_path,options=chrome_options)
        driver.maximize_window()
        driver.get("https://www.iso.org/obp/ui/#search")
        self.wait_for_element("//input[@class='v-textfield v-widget v-has-width']",driver)
        driver.find_element(By.XPATH,"//input[@class='v-textfield v-widget v-has-width']").send_keys(linkedin_location)
        self.wait_for_element("//input[@id='gwt-uid-12']",driver)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,"//input[@id='gwt-uid-12']"))).click()
        self.wait_for_element("//span[@class = 'v-button-caption']",driver)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,"//span[@class = 'v-button-caption']")))
        driver.find_elements(By.XPATH,"//span[@class = 'v-button-caption']")[1].click()
        self.wait_for_element("//div[@class='v-button v-widget breadcrumb v-button-breadcrumb']//span[@class='v-button-caption']",driver)
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"//div[@class='v-button v-widget breadcrumb v-button-breadcrumb']//span[@class='v-button-wrap']")))
        try:
            driver.find_elements(By.XPATH,"//div[@class='v-button v-widget breadcrumb v-button-breadcrumb']//span[@class='v-button-wrap']")[1].click()
        except:
            pass
        self.wait_for_element("//button[@class='v-nativebutton']",driver)
        country = driver.find_element(By.XPATH,"//button[@class='v-nativebutton']").text
        code = driver.find_element(By.XPATH,"//td[@class='v-grid-cell']").text.lower()
        driver.quit()
        #display.stop()
        return country,code
    
    def get_country(self,linkedin_loc):
        df = pd.read_csv(self.countries_code_path)[["en","alpha2"]]
        countries = list(df.en.values)
        
        country = linkedin_loc.split(',')[-1].strip()
        country = re.sub("’","'",country)
        #print("Countrty", country, end="\t")
        if country in countries:
            return country, df.loc[df['en'] == country]["alpha2"].values[0]
        if self.find_grouped_countries(linkedin_loc.strip()):
            country = self.find_grouped_countries(linkedin_loc.strip())
            if country in countries:
                return country, df.loc[df['en'] == country]["alpha2"].values[0]
        if self.geoloc(linkedin_loc):
            country = self.geoloc(linkedin_loc)
            if country in countries and linkedin_loc!="Other" :
                return country, df.loc[df['en'] == country]["alpha2"].values[0]
        
        try:
            country,code = self.iso_browser(linkedin_loc)
            print(country,code)
            countries = list(df.loc[df['alpha2'] == code]["en"].values)
            if countries != []:
                return countries[0],code
            else:
                return country,code
            
        except:
            return False
    
    def get_country_from_code(self,code):
        df = pd.read_csv(self.countries_code_path)[["en","alpha2"]]
        country = False
        try:
            number = len(df[df.alpha2 == code])
            #print(number)
            if number > 0:
                country = True
        except:
            pass

        return country   

    def geoloc_for_state(self,linkedin_location):
        res2 = self.get_gecoder(linkedin_location)
        if res2 == 'error in geocoder':
            return False
        else:
            Latitude , Longitude = res2[0], res2[1]
            location = self.locator.reverse(str(Latitude)+","+str(Longitude))
            address = location.raw['address']
            return address.get('state', '')
