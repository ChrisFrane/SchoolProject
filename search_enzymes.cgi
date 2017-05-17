#!/usr/local/bin/python3


import cgi, json
import os
import mysql.connector
import cgitb
import re
import sys

#cgitb.enable()
def main():

    print("Content-Type: application/json\n\n")
    form = cgi.FieldStorage()
    term = form.getvalue('search_term')
    searchType = form.getvalue('search_type')
    reviewStatus = form.getvalue('review_status')
    type1 = form.getvalue('type_1')
    type2 = form.getvalue('type_2')
    type3 = form.getvalue('type_3')
      
          
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
    # Connect to my restriction enzyme database !!!Change when adding to the server
    conn = mysql.connector.connect(user='cfrane1', password='password', 
                                   host='localhost', database='cfrane1')
    
    curs = conn.cursor()
    
    # The MySQL query differs in the WHERE section depending on what is selected
    # on a drop down menu in the form. Instead of making a query for each 
    # possibile query structure the column name which differs is entered as
    # a variable. To prevent possible abuse of an SQL injection by modifying
    # what is sent from the form, the variable is checked to make sure
    # it is one of the three expected values. If it isn't then the script
    # exits since it isn't a valid part of the query.
    if searchType !=  "enzyme.accession_num" and searchType != "gene_name" and searchType != "entry_name":
            sys.exit()
            
            
    qry = """SELECT enzyme.accession_num, entry_name,  
             recog_seq.sequence, recog_seq.primary_cut, 
             recog_seq.comp_cut, organism.name,
             protein_info.protein_name
             
             FROM enzyme
             
             JOIN protein_info ON protein_info.accession_num = enzyme.accession_num
             
             JOIN review_status ON review_status.review_status_id = enzyme.review_status_id
             
             JOIN ec_num ON ec_num.accession_num = enzyme.accession_num
             
             JOIN ec_info ON ec_num.number = ec_info.ec_num
             
             JOIN recog_seq ON recog_seq.recog_seq_id = enzyme.recog_seq_id
             
             JOIN organism ON organism.organism_id = enzyme.organism_id
             
             WHERE """ + searchType + """  LIKE %s
             
             AND review_status.status LIKE %s
             
             AND (ec_info.info LIKE %s
             OR ec_info.info LIKE %s
             OR ec_info.info LIKE %s)"""

    if term != None:  
        curs.execute(qry, ("%" + term + "%", reviewStatus, type1, type2, type3,))
    else:
        curs.execute(qry, ('', '', '', '', '',))
  
    results = { "match_count": 0, 'matches':list() }

    
    # Goes through each row found and adjusts the data for the resulting table.
    for(accession_num, entry_name, sequence, primary_cut, comp_cut,
        name, protein_name) in curs:
        
        # Makes sure that the primary cut and possible comp cut values are
        # integers so they can be used as such.
        if primary_cut != "Unknown":
            primary_cut = int(primary_cut)
        
            if comp_cut != None:
                comp_cut = int(comp_cut)
                     
 
            # Removes the notation for repeated nucleotides.
            expandedSeq = expand_seq(sequence)
             
     
            # Removes the notation for methylated nucleotides.
            expandedSeq = remove_methylation(expandedSeq)
 
            # Produces the compliment sequence to the recognition sequence.
            comp = compliment(expandedSeq)
          
            # Finds where the cut on the primary sequence would be located.
            cut1 = cut_site(expandedSeq, primary_cut)
        
            # If comp_cut = None then the recognition sequence is a palindrome so the
            # site of the cut on the compliment strand is len(seq) - primary_cut
            if comp_cut == None:
                cutLoc = len(expandedSeq) - primary_cut
                cut2 = cut_site(comp, cutLoc)
           
            # Otherwise the recognition sequence is not a palindrome so the other cut_site stored
            # needs to be used for the compliment strand.
            else:
                cutLoc = len(expandedSeq) - comp_cut
                cut2 = cut_site(comp, cutLoc)
            

            # Formating for display in the table.      
            cut1 = "5'-" + cut1 + "-3'"
            cut2 = "3'-" + cut2 + "-5'"
       
        # If there is no cut site in the the UniProt entry then have "Unknown" printed in the table.
        else:
            cut1 = "Unknown"
            cut2 = "Unknown"
        
        # Formating for display in the table.
        if sequence != "Unknown":
            sequence = "5'-" + sequence + "-3'"
            
        results["matches"].append({"accessionNum" : accession_num,
            "entryName" : entry_name, "sequence" : sequence, 
            "cut1" : cut1, "cut2" : cut2,
            "organism" : name, "proteinName" : protein_name})
            
        results["match_count"] += 1
    conn.close()
    
    print(json.dumps(results))
    
    
# This function will take a sequence and cut location and return a
# string like XXXX|XX where | is the cut location. In the case that the
# cut location is not part of the recognition site it will add characters
# so that the cut location is indicated.

def cut_site(seq, cutLoc):
    
    # Add 'N' characters in the case that the cut location is out of bounds
    # for the provided sequence.
    if len(seq) < cutLoc:
        seq = seq + ('N' * (cutLoc - len(seq)+1))
    
    seq = seq[0:cutLoc] + "|" + seq[cutLoc:len(seq)]
    
    return seq
    
    
# Some recognition sites use (#) to indicate multiple consecutive nucleotides.
# While this is nice when looking at the database it is nonfunctional in searches
# unless it is converted to {#} The problem with doing that is it doesn't work
# if you want the reverse compliment. This script expands that out.

def expand_seq(seq):

    m = re.search(r'\((\d)\)', seq)
    if m == None:
        return seq
    start = m.start()
    end = m.end()
    
    # Since there is already one copy of the nucleotide is in the sequnece
    # one less is needed.
    count = int(m.group(1)) -1
    seq = seq[0:start] + (seq[start-1:start] * count) + seq[end:len(seq)]
    return seq
    
def compliment(seq):
    # Since this requires replacements done in multiple steps
    # I will use the fact that str.replace() is case sensitive.
    # Therefore I will make sure that the provided sequence is
    # capitalized and replace with a lower case so something
    # doesn't get replaced twice.
    
    notation = {"A" : "t", "C" : "g", "T" : "a", "G": "c", "M" : "k",
                "K" : "m", "R" : "y", "Y" : "r", "B" : "v", "V" : "b",
                "D" : "h", "H" : "d"}
    
    # Make sure the sequence is upper case.
    seq = seq.upper()
    
    # Iterate through the notation dictionary to get the reverse compliment
    for key in notation:
        seq = seq.replace(key, notation[key])
        
    # Make the sequence uppercase again.
    seq = seq.upper()
    
    return seq

# Some restriction enzyme's recognition sequences have a methylated nucleotide
# shown as (Me). This needs to be removed when showing the cut sites in the table
# since it interfers.

def remove_methylation(seq):

    seq = seq.replace("(Me)", "")
    return seq
    
if __name__ == '__main__':
    main()
