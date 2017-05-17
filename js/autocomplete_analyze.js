// This is script that is used to get the desired Type-2 restriction enzymes
// from the database for use in autocomplete in analyze.html. I am keeping
// this seperate from the script for search_enzymes.html since the query
// used is different.

$(document).ready(function(){
    autocomplete();
    $(".change").change(function() {
        autocomplete();
    });
});

function autocomplete(){
    var availableTags = new Array();
    var frmStr = $('#analyze_seq').serialize();
    
    $.ajax({
        url: './get_autocomplete_analyze.cgi',
        type: 'GET',
        dataType: 'json',
        data: frmStr,
        
    success: function(data, textStatus, jqXHR) {
           //If the AJAX is successful it will iterate through the JSON
           //object and add each name from the database to the array.
           $.each(data, function(i, obj){
               availableTags.push(obj.tag); 
           })
          
        },
        // If for some reason the AJAX fails, through an error in an alert
        // box.
        error: function(jqXHR, textStatus, errorThrown){
            alert(errorThrown);
        }
    });
    
    // Make the search bar in the html form autocomplete with the relevant
    // names from the database.
    
    $('#search_term').autocomplete({
        minLength: 1,
        //Filters the autocomplete results and only displays 5.
        source: function(request, response) {
            var results = $.ui.autocomplete.filter(availableTags,
                          request.term);
                              response(results.slice(0, 5));
        }
    });
    
}

