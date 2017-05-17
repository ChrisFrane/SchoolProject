* ABOUT *

This project consists of four main parts:

1) create_database.sql: 

   A database designed to store information about restriction enzymes. 

2) parse.py:

   A python script that parses downloaded restriction enzyme text entries 
   downloaded from UniProt and adds the entries into the database.
   
3) search_enzymes.html, search_enzymes.cgi, get_autocomplete_search.cgi,
   autocomplete_search.js, search_enzymes.js:
   
   Web front-end and back-end for searching the database with various settings
   to limit the type of results along with the option to search by accession 
   number,gene name, or UniProt entry name. Autocomplete provides only 
   suggestions that fit the current settings and AJAX is used to display the 
   results without reloading the page.
   
4) analyze.html, analyze.cgi, get_autocomplete_analyze.cgi, 
   autocomplete_analyze.js, results.html:
   
   Web front-end and back-end for looking for restriction enzyme recognition
   sequences and returning the location of the cuts with the option to only
   show the enzymes that have a single recognition sequence in the input
   DNA sequence. Only Type-2 restriction enzymes with reviewed entries and
   known recognition and cut sites without methylation are valid.
   
   Input can either be through a text box or as an uploaded .fas file with
   a file taking priority if both are provided. Autocomplete uses AJAX
   to display valid terms with the option to search by gene name,
   accession number, or UniProt entry name. Data is displayed using Jinja2
   with the output being directed to the template html file results.html.
   
All the files except for the database can be obtained here:
    http://bfx.eng.jhu.edu/cfrane1/finalproject/cfrane1_final.tar.gz
   
* Detailed Usage *

  * parse.py *
    
	A text file is required as a command line argument. The file needs to be
	in the text format of UniProt entries. 
	
	NOTE: parse.py is designed to extract the recognition sequence and cut sites
	      from Type-1, Type-2, and Type-3 restriction enzymes. Files with entries
		  that are not of one of those types should work and be entered in the 
		  database although the function will not be collected and it will likely
		  treat the enzyme as having an unknown recognition sequence and cut sites.
		  
	Source files used to populate the database can be found here:
		http://bfx.eng.jhu.edu/cfrane1/finalproject/sources/
	



	
  *	Enzyme Search *
    
	HTML front-end is located here:
	    http://bfx.eng.jhu.edu/cfrane1/finalproject/search_enzymes.html
		
    1) Select what type of term you would like to search the database by.
		Options are "Gene Name", "Accession Number", and "UniProt Entry Name"

    2) Select the review status of the entries you want returned
		Options are "Reviewed Only", "Unreviewed Only", and "Both unreviewed and 
		reviewed"

    3) Select the restriction enzyme type you want to search. Multiple types can
	   be selected.
	   
	   Options are "1" for Type-1 restriction enzymes, "2" for Type-2 restriction
	   enzymes, and "3" for Type-3 restriction enzymes.
		
	4) Enter the search term. Autocomplete suggestions are based on the options 
	   selected above. Query uses LIKE so matches do not need to be exact. Not
 	   providing a term will result in no results being returned.
	   

	   
  * Analyze *
  
    HTML front-end is located here:
		http://bfx.eng.jhu.edu/cfrane1/finalproject/analyze.html
		
	1) Provide a linear DNA sequence either in the text area or uploaded as a 
	   .fas file. If both are provided the file takes priority. Format of the
	   entry needs to either be a pure DNA sequence or a single entry FASTA 
       format.	   
	    
	2) Choose to provide a term to limit the restriction enzymes used in the
	   analysis or leave the input box empty to use all valid enzymes. If
	   using a term select the search term type to use. Autocomplete will
	   suggest only valid terms.
	   
	3) Check the box to have only enzymes that cut the DNA sequence only once
	   displayed. Leave the box unchecked to have the cut site of all enzymes
	   used displayed.
	   
	4) Check the box if you would like to not show the sequence on the results 
	   page or not. This is useful if a long sequence is provided like in the 
	   example.
	   
	4) Submit.
	
	5) The numbers of the cut indicate the position of the nucleotide where 
	   cut occurs after.  The complimentary strand cut site is where the
	   strand complimentary of the provided sequence would be cut.
	   
	   * TEST FILES *
	     Two test files are provided. The first is located here:
		
			http://bfx.eng.jhu.edu/cfrane1/finalproject/test_input_1.fas
		 
		 This is the sequence for the fruit fly chromosome 4. Due to the
		 length of the sequence it is suggested that the option to not 
		 display the sequence on the results screen is selected. In addition
		 there should be no enzymes that have only one recognition sequence
		 on the chromosome.
		 
		 The second test file is here:
		 http://bfx.eng.jhu.edu/cfrane1/finalproject/test_input_2.fas
		
         This is the gene for human bone gla protein. Since it is significantly
		 shorter in length it is recommended to display the sequence on the
		 results page. Also some of the enzymes should only cut the sequence once.
		
	
	   
	   
