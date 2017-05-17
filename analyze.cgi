#!/usr/local/bin/python3

import urllib
import sys
import re
import mysql.connector
import cgi
import jinja2
import cgitb

# This script uses a web form to take a DNA sequence in FASTA format and
# connecting to my restriction enzyme database determine which enzymes
# will cut the sequence and where.

# Options in the form will allow for the limitation of which enzymes are used
# by gene name or accession number. In addition there is an option that only
# gives the enzymes that cut the sequence exactly one time.

cgitb.enable()

class Enzyme():
    
    def __init__(self, accessionNum, geneName, recogSeq,
                 recogSeqRegex, cut1, cut2):
        self.cutLoc = list()
        self.accession = accessionNum
        self.gene = geneName
        self.recogSeq = recogSeq
        self.recogSeqRegex = recogSeqRegex
        self.cutLoc.append(cut1)
        self.cutLoc.append(cut2)
        self.cuts = None

    
    # A class function that will be used to check if the enzyme has two locations it cuts.
    # This will indicate that the sequence is not a palindrome and the reverse compliment
    # will need to be checked too.
    def two_cut_sites(self):
        if self.cutLoc[1] == None:
            return False
        else:
            return True
    
    # The loc will be the start
    def add_cut(self, loc):
        self.cuts.append(loc)
    
    def add_cut_comp(self, loc):
        self.cutsComp.append(loc)


def main():
    
    print("Content-type: text/html\n\n")    
    templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
    env = jinja2.Environment(loader=templateLoader)
    template = env.get_template('results.html')

    # Connect to the database
    conn = mysql.connector.connect(user='cfrane1', password='password',
                                   host='localhost', database='cfrane1')
                                   
    curs = conn.cursor()
    
    # Creates an object from the form that directs to this cgi file
    form = cgi.FieldStorage()
    
    inputSequence = form.getvalue("sequence")
    searchType = form.getvalue("search_type")
    term = form.getvalue("search_term")
    inputFile = form.getvalue("sequence_file")
    cutOnce = form.getvalue("cut_once")
    hideSeq = form.getvalue("hide_seq") 
     
    inputFile = inputFile.decode("utf-8")  
    # Have a file take priority.
    if inputFile != '':
        inputSequence = inputFile       
            
    # Check to see if an input sequence was provided.
    if inputSequence == ''  or re.match(r'\s+$', inputSequence) :
        print("No input sequence provided.")
        sys.exit() 

    # Makes it so that if no search term is provided it will use all valid enzymes.
    if term == None:
        term = ''

    
    # Get rid of the FASTA header from the search sequence.
    inputSequence = re.sub('>.+[\n\]]', '', inputSequence, 1)
    
    if re.search('>', inputSequence):
        print("Multiple FASTA sequences were provided. Please only submit one.")
        sys.exit()
   
    # Remove all whitespace from the input sequence.
    inputSequence = re.sub('\s', '', inputSequence) 

    inputSequence = inputSequence.upper()

    # Remove unsequenced heterochromatin from the input sequence.
    inputSequence = re.sub('N', '', inputSequence)
      

    # Make sure that the provided input is a nucleotide sequence
    if re.search(r'[^GCTA]', inputSequence):   
        print("Provided input is not a valid DNA sequence.")
        sys.exit()
         
    if searchType != "enzyme.accession_num" and searchType != "gene_name" and searchType != "entry_name":
        print("Invalid search type!")
        sys.exit()
       
    qry = """SELECT enzyme.accession_num, gene_name, recog_seq.sequence,
             recog_seq.primary_cut, recog_seq.comp_cut
             
             FROM enzyme
             
             JOIN recog_seq ON recog_seq.recog_seq_id = enzyme.recog_seq_id
             
             JOIN ec_num ON ec_num.accession_num = enzyme.accession_num
             
             JOIN ec_info ON ec_num.number = ec_info.ec_num
             
             JOIN review_status ON review_status.review_status_id = enzyme.review_status_id
             
             WHERE ec_info.info LIKE '%Type-2%'
             
             AND review_status.status = 'reviewed'
             
             AND """ + searchType + """ LIKE %s
             
             AND recog_seq.sequence != 'Unknown'
             
             AND recog_seq.primary_cut != 'Unknown'
             
             AND recog_seq.sequence NOT LIKE '%(Me)%'
             """
             
       
    curs.execute(qry, ("%" + term + "%",))
    

    # Create a list to store the enzymes that will be passed to the template.
    enzymes = list()


    # Iterate through the entries from the query and search the
    for (accession_num, gene_name, sequence, primary_cut, comp_cut) in curs:
        # Make sure that primary_cut and comp_cut are integers.
        primaryCut = int(primary_cut)
        
        if comp_cut != None:
            compCut = int(comp_cut)
        else:
            compCut = None
        # Modify restriction enzyme sequence so it is useable in a regular
        # expression.  

        recogSeqRegex = convert_regex(expand_seq(sequence))
     
        # Create an instance of the enzyme class to hold all the information.
        
        enzyme = Enzyme(accession_num, gene_name, sequence, recogSeqRegex,
                        primaryCut, compCut)
                        
        # Find the cuts for this enzyme.
        
        find_cuts(inputSequence, enzyme, cutOnce)
        
        if enzyme.cuts != None:
            enzymes.append(enzyme)
    conn.close()
    
    # Format the input sequence so that it can be better displayed on the results
    # page.
    if hideSeq == None:
        formatedSeq = format_sequence(inputSequence)
    else:
        formatedSeq = zip(list(), list())
    print(template.render(enzymes=enzymes, sequence=formatedSeq))
    

### Functions ###

# While a number of restriction enzymes recognize palindromic sequences and
# therefore only one sequence needs to be used on one strand to determine where
# it should get cut. However in the case that it is not palindromic this function
# will get the reverse compliment so only one part of the recognition sequence
# needs to be stored in the database.

def reverse_compliment(seq):
    # Since this requires replacements done in multiple steps
    # I will use the fact that str.replace() is case sensitive.
    # Therefore I will make sure that the provided sequence is
    # capitalized and replace with a lower case so something
    # doesn't get replaced twice.
    
    seq = seq.upper()
    seq = seq.replace("C", "g") 
    seq = seq.replace("G", "c")
    seq = seq.replace("T", "a")
    seq = seq.replace("A","t")
    seq = seq.upper()
    
    # Now to reverse the string and return.
    seq = seq[::-1]
    return seq

# Some restriction enzymes are flexible in what sequence they recognize
# and therefore positions that can have multiple nucleotides that work
# use alternative notation. However this is not useful for trying to
# search a sequence for the recognition sites so this function takes a 
# dictionary and replaces the alternative notation with a regex usable
# notation to indicate the possible nucleotides.

# Since it is only working on the alternative notation for nucleotides
# there is no problem of accidently replacing a site multiple times.

def convert_regex(seq):
    

    # The dictionary that will be used to replace alternative nucleotide
    # notation.
    
    notation = {'W':'[AT]','S':'[GC]','M':'[AC]','K':'[GT]','R':'[AG]',
        'Y':'[CT]','B':'[CGT]','D':'[AGT]','H':'[ACT]','V':'[ACG]','N':'[ACGT]'}
    
    # Make sure sequence is uppercase.
    seq = seq.upper()
    
    for key in notation:
        seq = seq.replace(key, notation[key])
    
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

# This takes a DNA sequence and an enzyme class and stores all
# the locations of the cuts performed on the sequence by the restriction
# enzyme into the enzyme class.
def find_cuts(seq, enzyme, cutOnce):
    m = re.finditer(enzyme.recogSeqRegex, seq)
    cutSite = list()
    cutSiteComp = list()
    
    # Check to see if the recognition sequence is a palindrome, if not
    # it needs to also find all the appearences of the reverse 
    # compliment in the input sequence.
    if enzyme.two_cut_sites():
        for cut in m:
            
            cut1 = cut.start() + enzyme.cutLoc[0]
            cut2 = cut.start() + len(enzyme.recogSeq) - enzyme.cutLoc[1]
            
            # Make sure the cut sites are actually on the DNA sequence
            if not cut1 > len(seq) and not cut2 > len(seq):
                cutSite.append(cut1)
                cutSiteComp.append(cut2)
                
        # Checks for matches to the reverse compliment.
        reverseComp = reverse_compliment(enzyme.recogSeq)
        m = re.finditer(reverseComp, seq)
        for cut in m:
            cut1 = cut.start() + enzyme.cutLoc[1]
            cut2 = cut.start() - len(enzyme.recogSeq) - enzyme.cutLoc[0]
            # Make sure the cut sites are actually on the DNA sequence
            if not cut1 < 0 and not cut2 < 0:
                cutSite.append(cut1)
                cutSiteComp.append(cut2)
    else:
        for cut in m:
            cutSite.append(cut.start() + enzyme.cutLoc[0])
            cutSiteComp.append(cut.start() + len(enzyme.recogSeq) - enzyme.cutLoc[0])
   
    if cutOnce != None and len(cutSite) == 1:    
        enzyme.cuts = zip(cutSite, cutSiteComp)      
    elif cutOnce == None:
        enzyme.cuts = zip(cutSite, cutSiteComp)        
    return enzyme
    

def format_sequence(seq):
    curPos = 0
    pos = 0
    lines = list()
    linePos = list()
    while pos < len(seq):
        line = ''    
        while curPos < (pos + 60):
            line = line + ' ' + seq[curPos: (curPos + 10)]
            curPos = curPos + 10
        lines.append(line)
        linePos.append(str(pos+1))         
        pos = curPos
    sequence = zip(linePos, lines)
    return sequence
    
if __name__ == "__main__":
    main()
    
