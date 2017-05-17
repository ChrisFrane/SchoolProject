$(document).ready(function(){
    autocomplete();
    $(".change").change(function() {
        autocomplete();
    });
});

function autocomplete(){
    var availableTags = new Array();
    var frmStr = $('#search_enzymes').serialize();
   
    $.ajax({
        url: './get_autocomplete_search.cgi',
        type: 'GET',
        dataType: 'json',
        data: frmStr,       

        success: function(data, textStatus, jqXHR) {
           //If the AJAX is successful it will iterate through the JSON
           //object and add each name from the database to the array.
          
           $.each(data, function(i, obj){
               availableTags.push(obj.tag); 
           }); 
           
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

