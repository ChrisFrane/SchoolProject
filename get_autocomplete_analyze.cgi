#!/usr/local/bin/python3

import json
import os
import mysql.connector
import cgitb
import cgi
import sys

#cgitb.enable()
def main():
    print("Content-Type: application/json\n\n")
    form = cgi.FieldStorage()
    searchType = form.getvalue('search_type')    
     
    conn = mysql.connector.connect(user = 'cfrane1', password = 'password', 
                                   host = 'localhost', database =
                                   'cfrane1')
    cursor = conn.cursor()
    

    # The MySQL query differs in the WHERE section depending on what is selected
    # on a drop down menu in the form. Instead of making a query for each 
    # possibile query structure the column name which differs is entered as
    # a variable. To prevent possible abuse of an SQL injection by modifying
    # what is sent from the form, the variable is checked to make sure
    # it is one of the three expected values. If it isn't then the script
    # exits since it isn't a valid part of the query.
    
    if searchType !=  "enzyme.accession_num" and searchType != "gene_name" and searchType != "entry_name":
            sys.exit()

    
    qry = """SELECT """ + searchType + """ FROM enzyme

             JOIN review_status 

             ON review_status.review_status_id = enzyme.review_status_id

             JOIN ec_num

             ON ec_num.accession_num = enzyme.accession_num

             JOIN ec_info

             ON ec_info.ec_num = ec_num.number

             JOIN recog_seq

             ON recog_seq.recog_seq_id = enzyme.recog_seq_id

             WHERE review_status.status = 'Reviewed'

             AND recog_seq.sequence != 'Unknown'

             AND recog_seq.primary_cut != 'Unknown'

             AND recog_seq.sequence NOT LIKE '%(Me)%'

             AND ec_info.info LIKE '%Type-2%'
             """
             
             
    cursor.execute(qry,)

    
    names = set()
    availableTags = list()
    
    # Iterates through the data obtained from the query and if the entry
    # is not empty or not None then it stores it in the set. Since the
    # set can only contain unique entries it prevents possible duplicates
    # showing up in the autocomplete suggestions.
    for (value,) in cursor:
        if value != '' or value != None:
            names.add(value)
     
    conn.close()
    
    # Iterates through the set and stores it in availableTags in JSON format.
    for name in names:
        availableTags.append({"tag":name})
    
    # Passes the information to the javascript file.
    print(json.dumps(availableTags))
if __name__ == '__main__':
    main()
             
