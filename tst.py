import csv
import os
from stored_object import StoredObject


objs = StoredObject.load_from_csv()

for obj in objs:   
    if obj.instrument =="SAMIR":
        print(obj.missing_data)
        