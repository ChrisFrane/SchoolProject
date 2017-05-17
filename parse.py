#!/usr/local/bin/python3

# This script takes a "Text" file format of a collection of restriction
# enzymes downloaded from UniProt as an argument. In order to make sure that
# the file is appropriate it is checked to make sure it is in the format expected
# and that the entries are restriction enzymes.

# Then the script will parse for information relavant for the database. This includes
# the protein name, gene name, accession number, reviewed status, protein length, 
# recognition site, cut site, and organism.

# After all the information is collected for a single entry then the script will
# enter it into restriction enzyme database.

import mysql.connector
import sys
import re

# A class that will hold the parsed information of the restriction enzyme entries.
class EntryInfo:
    def __init__(self):
        self.id = ''
        self.geneName = None
        self.proteinName = None
        self.accessionNum = ''
        self.reviewedStatus = ''
        self.reviewedInfo = ''
        self.recogSeq = "Unknown"
        self.cutLoc1 = "Unknown"
        self.cutLoc2 = None
        self.organism = "Unknown"
        self.seq = ''
        
        # A entry can have multiple EC numbers. While there are only
        # 3 that are relevant identifying the type of restriction
        # enzyme an entry is all of them will be included in the database.
        self.ecNum = list()
        
        # The function section of an entry is multiple lines. In order
        # to be able to look at all of the information at once each line
        # will be stored in a string first.
        self.functionLines = ''


def main(argv):
    # Check to make sure that an argument is provided.
    if len(sys.argv) < 2:
        print("No file provided in argument.")
        sys.exit()
        
    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print("Cannot open", sys.argv[1])
        sys.exit()
        
    parseFile(f)
    



def parseFile(myFile):
    conn = mysql.connector.connect(user='cfrane1', password='password',
                                   host='localhost', database='cfrane1',
                                   buffered=True)
    curs = conn.cursor()
    
    # Triggers for cases where multiple lines of data
    # need to be collected.
    sequence = False
    function = False
    
    info = EntryInfo()
    for line in myFile:
    
        # Strip newline characters from the line.
        line = line.strip()
        
        # New entries are started with // so that will be used as the
        # spot to store the previous entry into the database and
        # reinitialize the info variable with a new EntryInfo object.
        
        if line.startswith("//"):
              
            # The organism line always ends in a period. For some cases such
            # as the organism Bacillus sp. the period is part of the name.
            # This checks to see if the last word in the organism name is
            # 'sp' and if not strips the ending period. There may be
            # other organisms that 'need' the ending period and in that
            # case this would need to be updated with more expections.

            if info.organism != "Unknown":
                m = re.search(r'\s*([\S]+)\.$', info.organism)
                if m.group(1) != "sp": 
                    info.organism = info.organism.rstrip('.')

            # This parsing script is designed to also work with unreviewed
            # restriction enzyme entries from UniProt. Some of those entries
            # do not have a gene name listed even though the gene name is
            # often part of the protein name. This attempts to fill in the
            # gene name by collecting it from the protein name.

            if info.geneName == None and not info.proteinName == None:
                m = re.search(r'(nuclease|enzyme|,)\s([A-Z][A-Za-z]{3,5})', info.proteinName)
                if m != None:
                    info.geneName = m.group(2)[0:1].lower() + m.group(2)[1:len(m.group(2))]
            
            add_to_database(info.accessionNum,info.geneName, info.id, 
                            info.organism, info.reviewStatus, info.reviewInfo,
                            info.recogSeq, info.cutLoc1, info.cutLoc2,
                            info.seq, info.proteinName, info.ecNum,
                            curs, conn)
            sequence = False
            info = EntryInfo()
        
        # Collect entry name (which is unique but not stable), and review status.
        # Protein length can be calculated from the sequence so it isn't stored.
        if line.startswith("ID "):
            m = re.search(r'ID\s+(\S+)\s+([^;]+);', line)
            info.id = m.group(1)
            info.reviewStatus = m.group(2)

        
        # Collect accession number which is unique and stable. This will be
        # used as a primary key for the main table of the database.
        if line.startswith("AC "):
            m = re.search(r'AC\s+([^;]+)', line)
            info.accessionNum = m.group(1)
         
        # Collect the recommended protein name which is not unique.
        if line.startswith("DE   RecName"):
            m = re.search(r'=([^;^{]+)', line)
            info.proteinName = m.group(1)
        elif line.startswith("DE   SubName"):
            m = re.search(r'=([^;^{^(]+)', line)
            info.proteinName = m.group(1)
        
        # Some enzymes have multiple EC numbers associated
        # with them. While there are only three EC numbers 
        # of interest for the scope of this database, that
        # being the ones for Type-1, Type-2, and Type-3
        # restriction enzymes, all the EC numbers for each
        # enzyme will be stored in the database.

        if re.match(r'DE\s+EC=', line):
            m = re.search(r'=([^ ^;]+)', line)
            info.ecNum.append(m.group(1))


        # Collect gene name if possible. If at the end of the entry a gene
        # name wasn't collected the script will try to collect it from
        # the protein name.
        if line.startswith("GN   Name"):
            m = re.search(r'=([^;^\s]+)', line)
            info.geneName = m.group(1)

        
        # Collect the organism name. This can be multiple lines due to the
        # naming including information like strain.
        if line.startswith("OS "):
            if info.organism == "Unknown":
                info.organism = ''
            m = re.search(r'OS\s+(.+)', line)
            info.organism = info.organism + m.group(1)

        # This will trigger when the function section of the current entry
        # is done. The parsing for information on the recognition sites and
        # cleave sites are then performed.
        if (line.startswith("CC   -!-") or not line.startswith("CC")) and function:
            function = False
            
            # This makes it so only the relevant information is stored instead
            # of the 'header' for each line.
            info.functionLines = info.functionLines[15:]
            
            
            # The term 'respectively' in the function line seems to indicate
            # that the recognition sequence for the enzyme is not palindromic
            # which means that two cut sites need to be collected. 
            if re.search(r'respectively', info.functionLines):
                # Only one strand recognized is stored since the other
                # can be determined through finding the reverse complement.
                m = re.search(r'([GTAC]+)[^GTAC]+[GTAC]+', info.functionLines)
                info.recogSeq = m.group(1)
                r = re.search(r'(\d+).+and (\d+)', info.functionLines)
                info.cutLoc1 = int(r.group(1))
                info.cutLoc2 = -int(r.group(2))

            # Otherwise either the function lines do not have the recognition
            # sequence and it will be considered 'unknown' for the entry or
            # the recognition sequence is a palindrome. 
            else:
                m = re.search(r"sequence[\s\d/'-]*([GTCANRYSWKMBDHV(Me)\d]+)\-*\d*", info.functionLines)
                if not m == None:
                    info.recogSeq = m.group(1)

                if re.search(r'cleaves (\S+) [GACTN]-(\d)', info.functionLines):
                    
                    r = re.search(r'cleaves (\S+) [GTCAN]-(\d)', info.functionLines)
                    # If the function line says it cleaves 'before' a nucleotide
                    # then 1 needs to be subtracted from the location so that
                    # it is the proper cut location.
                    if r.group(1) == "before" :
                        info.cutLoc1 = int(r.group(2)) - 1
                    if r.group(1) == "after":
                        info.cutLoc1 = int(r.group(2))
                     

            
        # The function section of the entry contains multiple lines and in order
        # to parse the whole section this block will collect everything in the section
        # using the function variable which is turned off when the next section in the entry
        # starts where it is then parsed.
        if line.startswith("CC   -!- FUNCTION") or function:
            function = True
            m = re.search(r'CC\s+(.+)', line)
            info.functionLines = info.functionLines + ' ' + m.group(1)
        
        
        # This will get the review info about the enzyme.
        if line.startswith("PE "):
            m = re.search(r': ([^;]+)', line)
            info.reviewInfo = m.group(1)

        if sequence == True:
            seq = re.sub(r'\s', '', line)
            info.seq = info.seq + seq

        if line.startswith("SQ "):
            sequence = True;
    conn.close()


# Functions that are used to insert into the database.
            
# Add to the organism table and also gets the approriate foreign
# key for the enzyme table.        
def add_organism(organism, curs, conn):
    if organism == '':
        return
    qry = "SELECT organism_id FROM organism WHERE name = %s"
    orgId = curs.execute(qry, (organism,))
    if curs.rowcount == 1:
        orgId = curs.fetchone()
        return orgId[0]
    elif curs.rowcount == 0:
        insert = "INSERT INTO organism (name) VALUES (%s)"
        curs.execute(insert, (organism,))
        conn.commit()
        curs.execute(qry, (organism,))
        orgId = curs.fetchone()
        return orgId[0]

# Add to the review_status table and also gets the appropriate foreign key
# for the enzyme table.
def add_review_status(reviewStatus, curs, conn):
    if reviewStatus == '':
        return
    qry = "SELECT review_status_id FROM review_status WHERE status = %s"
    statusId = curs.execute(qry, (reviewStatus,))
    if curs.rowcount == 1:
        statusId = curs.fetchone()
        return statusId[0]
    elif curs.rowcount == 0:
        insert = "INSERT INTO review_status (status) VALUES (%s)"
        curs.execute(insert, (reviewStatus,))
        conn.commit()
        curs.execute(qry, (reviewStatus,))
        statusId = curs.fetchone()
        return statusId[0]

# Add to the review_info table and also gets the appropriate foreign key
# for the enzyme table.
def add_review_info(reviewInfo, curs, conn):
    if reviewInfo == '':
        return
    qry = "SELECT review_info_id FROM review_info WHERE info = %s"
    curs.execute(qry, (reviewInfo,))
    if curs.rowcount == 1:
        infoId = curs.fetchone()
        return infoId[0]
    elif curs.rowcount == 0:
        insert = "INSERT INTO review_info (info) VALUES (%s)"
        curs.execute(insert, (reviewInfo,))
        conn.commit()
        curs.execute(qry, (reviewInfo,))
        infoId = curs.fetchone()
        return infoId[0]

# Add to the recog_seq table and also gets the approrpiate foreign key for
# the enzyme table.
def add_recog_seq(recogSeq, cutsite1, cutsite2, curs, conn):
    qry = """SELECT recog_seq_id FROM recog_seq WHERE sequence = %s AND primary_cut = %s
             AND (comp_cut = %s OR comp_cut IS NULL)"""
    curs.execute(qry, (recogSeq, cutsite1, cutsite2,))
    if curs.rowcount == 1:
        recogSeqId = curs.fetchone()
        return recogSeqId[0]
    elif curs.rowcount == 0:
        insert = "INSERT INTO recog_seq (sequence, primary_cut, comp_cut) VALUES (%s, %s, %s)"
        curs.execute(insert, (recogSeq, cutsite1, cutsite2,))
        conn.commit()
        curs.execute(qry, (recogSeq, cutsite1, cutsite2,))
        recogSeqId = curs.fetchone()
        return recogSeqId[0]

# Adds to the enzyme, protein_info, and ec_num tables.
def add_enzyme(accessionNum, geneName, entryName, orgId, statusId, infoId, 
               recogSeqId, seq,  proteinName, ecNum, curs, conn):
    if not(geneName == '' or entryName == '' or seq == '' or proteinName == ''):
        
        qry = "SELECT accession_num FROM enzyme WHERE accession_num = %s"
        curs.execute(qry, (accessionNum,))
        if curs.rowcount == 0:
            insert = """INSERT INTO enzyme (accession_num, gene_name, organism_id,
                        review_info_id, review_status_id, recog_seq_id, entry_name) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            curs.execute(insert, (accessionNum, geneName, orgId, infoId, statusId, 
                         recogSeqId, entryName,))
                        
            conn.commit()

            # Enter the EC numbers.
            insert = "INSERT INTO ec_num (accession_num, number) VALUES (%s, %s)"
            for num in ecNum:
                curs.execute(insert, (accessionNum, num,))
                conn.commit
            
            # Enter the information for protein_info table.
            insert = """INSERT INTO protein_info (accession_num, sequence, protein_name) VALUES 
                        (%s, %s, %s)"""
            curs.execute(insert, (accessionNum, seq, proteinName,))
            conn.commit()
            
# Function that uses the previous functions to add all aspects of an entry
# into the database.
def add_to_database(accessionNum, geneName, entryName, org, reviewStatus, 
                    reviewInfo, recogSeq, cut1, cut2, proteinSeq, proteinName,
                    ecNum, curs, conn):
    orgId = add_organism(org, curs, conn)
    infoId = add_review_info(reviewInfo, curs, conn)
    statusId = add_review_status(reviewStatus, curs, conn)
    recogSeqId = add_recog_seq(recogSeq, cut1, cut2, curs, conn)
    add_enzyme(accessionNum, geneName, entryName, orgId, statusId, infoId, 
               recogSeqId, proteinSeq, proteinName, ecNum, curs, conn)
    
           
if __name__ == "__main__":
    main(sys.argv)
    
    

