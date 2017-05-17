$(document).ready(function(){
    $("#submit").click(function() {
        $('*').css('cursor', 'progress'); 
        runSearch();
    });
});

function runSearch( term ) {
    // hide and clear the previous results, if any
    $('#results').hide();
    $('tbody').empty();
    
    var frmStr =  $('#search_enzymes').serialize();
    
    $.ajax({
        
        url: './search_enzymes.cgi',
        dataType: 'json',
        data: frmStr,
                    
        success: function(data, textStatus, jqXHR) {
            $('*').css('cursor', 'default');
            processJSON(data);
        },
        error: function(jqXHR, textStatus, errorThrown){
            $('*').css('cursor', 'default');
            alert("Failed to perform enzyme search! textStatus: (" + textStatus +
                ") and errorThrown: (" + errorThrown + ")");
        }
    });
}

function processJSON( data ) {
    // set the span that list the number of hits
    $('#match_count').text( data.match_count ) ;
    
    // this will be used to keep track of row identifiers
    var next_row_num = 1;
    
    // iterate over each match and add a row to the result table for each
    $.each( data.matches, function(i, item) {
        var this_row_id = 'result_row_' + next_row_num++;
        
        // create a row and append it to the body of the table
        $('<tr/>', { "id" : this_row_id } ).appendTo('tbody');
        
        // add the accession number column
        $('<td/>', { "text" : item.accessionNum } ).appendTo('#' + this_row_id);
        
        // add the UniProt entry name column
        $('<td/>', { "text" : item.entryName } ).appendTo('#' + this_row_id);
        
        
        // add the protein name column
        $('<td/>', { "text" : item.proteinName } ).appendTo('#' + this_row_id);
        
        // add the recognition sequence column
        $('<td/>', { "text" : item.sequence } ).appendTo('#' + this_row_id);
        
        // add the top strand cut site column
        $('<td/>', { "text" : item.cut1 } ).appendTo('#' + this_row_id);
        
        // add the bottom strand cut site column
        $('<td/>', { "text" : item.cut2} ).appendTo('#' + this_row_id);
        
        // add the organism column
        
        $('<td/>', { "text" : item.organism } ).appendTo('#' + this_row_id);
    });
    $('#results').show();   
}

