#!/usr/local/bin/python3

import json
import os
import mysql.connector
import cgitb
import cgi
import sys

cgitb.enable()
def main():
    print("Content-Type: application/json\n\n")
    form = cgi.FieldStorage()
    searchType = form.getvalue('search_type')
    status = form.getvalue('review_status')
    type1 = form.getvalue('type_1')
    type2 = form.getvalue('type_2')
    type3 = form.getvalue('type_3')
    
    conn = mysql.connector.connect(user = 'cfrane1', password = 'password', 
                                   host = 'localhost', database = 'cfrane1')
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


    if type1 != None:
        type1 = "%" + type1 + "%"
    else:
        type1 = ''
    
    if type2 != None:
        type2 = "%" + type2 + "%"
    else:
        type2 = ''
        
    if type3 != None:
        type3 = "%" + type3 + "%"
    else:
        type3 = ''
        
    qry = """SELECT """ + searchType + """ FROM enzyme
             JOIN review_status rs
             ON rs.review_status_id = enzyme.review_status_id
             JOIN ec_num
             ON ec_num.accession_num = enzyme.accession_num
             JOIN ec_info
             ON ec_info.ec_num = ec_num.number
             WHERE
             rs.status LIKE %s
             AND 
             (ec_info.info LIKE %s
             OR
             ec_info.info LIKE %s
             OR
             ec_info.info LIKE %s)
             """
             
    cursor.execute(qry, (status, type1, type2 , type3,))

    
    names = set()
    availableTags = list()
    
    # Iterates through the data obtained from the query and if the entry
    # is not empty or not None then it stores it in the set. Since the
    # set can only contain unique entries it prevents possible duplicates
    # showing up in the autocomplete suggestions.
    for (value,) in cursor:
        if value != '' and value != None:
            names.add(value)
     
    conn.close()
    
    # Iterates through the set and stores it in availableTags in JSON format.
    for name in names:
        availableTags.append({"tag":name})
    
    # Passes the information to the javascript file.
    print(json.dumps(availableTags))
if __name__ == '__main__':
    main()
