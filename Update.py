import context
import pymongo
import config

azure_config = config.Azure_config()
client = pymongo.MongoClient(azure_config.COSMOS_CONNECTION)
mongo_data1 = client.get_database(name=azure_config.DB_NAME).get_collection(name='testing_chronjob')

#file = open('/home/celebal/Pipeline/logs/chronejob.txt','w')
cursor = mongo_data1.find({})
# Get the experiment run context
run = Run.get_context()

from pyvirtualdisplay import Display
display = Display(visible=0, size=(1920, 1080))  
display.start()
for document in cursor:
    #print(document)
    #file.write('started\n')
    scrape = context.context(document["_id"],document["Compnay_url"],100)
    #file.write('1\n')
    record = scrape.Scraper()
    #file.write('2\n')
    query = {"_id":document["_id"]}
    #file.write('3\n')
    new_values = {"$set":{'Glassdoor' : record['Glassdoor'], "Linkedin" : record["Linkedin"], "Website":record["Website"]}}
    #file.write('4\n')
    mongo_data1.update_one(query,new_values)
    #file.write('5\n')
    #file.write("Updated : {} -> {}\n".format(document["_id"],document["Compnay_url"]))
    #file.write('ended\n')
#file.close()
display.stop()
run.complete()
