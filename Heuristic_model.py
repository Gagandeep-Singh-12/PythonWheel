import pandas as pd
import re
class Model():
    def __init__(self,Census_age,Census_income,Census_pop):
        self.Census_age_path = Census_age
        self.Census_income_path =Census_income
        self.Census_pop_path = Census_pop

    def Country(self,sales,countries,Revenue):
        uni_countries = list(set(countries))
        Country_Dist={}
        total = 0
        for i in uni_countries:
            for j in range(len(countries)):
                if i == countries[j] and i!="NA":
                    sales_value = int(re.sub(",","",sales[j]))
                    total+=sales_value
                    if i not in Country_Dist.keys():
                        Country_Dist[i] = sales_value
                    else:
                        Country_Dist[i] += sales_value

        for i in Country_Dist.keys():
            Country_Dist[i] /= total
            Country_Dist[i] *= Revenue
        return Country_Dist


    def Census(self,State_List,rev):
        State={}
        tot=0

        uni_state=list(set(State_List))
        if len(uni_state) == 1:
            State[uni_state[0]] = rev
            return State
        for s in uni_state:
            age_df = pd.read_csv(self.Census_age_path)
            income_df = pd.read_csv(self.Census_income_path)
            pop_df = pd.read_csv(self.Census_pop_path)

            income = income_df[income_df["state_code"] == s.upper()]["median_income"].values[0]
            Age = age_df[age_df["state_code"] == s.upper()]["median_age"].values[0]
            pop = pop_df[pop_df["state_code"] == "CA"]["population"].values[0]
            Value = income*2.5 + Age*0.1 + pop*0.1
            State[s] = Value
            tot+=Value
        for k in State.keys():
            State[k]/=tot
            State[k]*=rev
        return State

    def State_level(self,Country_Dist,Combined,Website):
        State_Dist ={}
        for country in Country_Dist.keys():
            if country not in Combined.keys():
                continue
            if country == "us":
                State_Dist["us"] = self.Census(Combined["us"],Country_Dist["us"])
            else:
                State={}
                val = 0            
                for City in list(set(Combined[country])):
                    flag = -1
                    City = City.lower()
                    for loc in Website["web_data"]:
                        loc = loc.lower()
                        if City in loc or City==loc:
                            State[City] = 2
                            val+=2
                            flag = 0
                            break
        
                    if flag == -1:
                        State[City]=1
                        val+=1

                for k in State.keys():
                    State[k]/=val
                    State[k]*=Country_Dist[country]
                State_Dist[country] = State
        return State_Dist

    def Distribute(self,Sales,Linkedin,Glassdoor,Website,Revenue):
        Combined={}
        Linkedin_countries = list(Linkedin.keys())
        Glassdoor_countries = list(Glassdoor.keys())
        Country_Dist=self.Country(Sales["sales_count"],Sales["country"],Revenue)
        #return Country_Dist

        for i in list(set(Linkedin_countries+Glassdoor_countries)):
            if i in Linkedin_countries and i in Glassdoor_countries:
                Combined[i] = Linkedin[i]+Glassdoor[i]
            elif i in Linkedin_countries:
                Combined[i] = Linkedin[i]
            elif i in Glassdoor_countries:
                Combined[i] = Glassdoor[i]
        
        State_Dist = self.State_level(Country_Dist, Combined, Website)

        return Country_Dist, State_Dist