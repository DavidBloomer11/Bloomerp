function setM2MValue(pk, displayText, widgetName) {
    // Get the display id for the widget
    input_div = document.getElementById(`${widgetName}_input_div`)

    // Create a new input element if it doesn't exist
    if (document.getElementById(`${widgetName}_${pk}`) == null) {
        let newInput = document.createElement("input");
        newInput.setAttribute("value", pk);
        newInput.id = `${widgetName}_${pk}`;
        newInput.name = widgetName;
        input_div.appendChild(newInput);

        // Create a new span element to display the selected object
        view_div = document.getElementById(`${widgetName}_view_div`);
        let newSpan = document.createElement("span");
        newSpan.className = "badge label-span";
        newSpan.id = `${widgetName}_span_${pk}`;
        newSpan.innerHTML = displayText;
        newSpan.onclick = function() {removeM2M(widgetName, pk)};
        view_div.appendChild(newSpan);
    }
}

function removeM2M(widgetName, pk) {
    // Get the input and view divs for the widget
    let input_div = document.getElementById(`${widgetName}_input_div`);
    let hiddenInput = document.getElementById(`${widgetName}_${pk}`);
    let view_div = document.getElementById(`${widgetName}_view_div`);
    
    // Remove the hidden input element for the selected item
    if (hiddenInput) {
        input_div.removeChild(hiddenInput);
    }

    // Find the correct span element to remove
    let spanToRemove = document.getElementById(`${widgetName}_span_${pk}`);
    if (spanToRemove) {
        view_div.removeChild(spanToRemove);
    }
}

function setForeignKeyValue(pk, displayText, widgetName) {
    // Set the hidden input value to the selected object's pk
    let hiddenInputId = widgetName + "_hidden_input";
    let hiddenInput = document.getElementById(hiddenInputId);

    console.log(hiddenInput)

    hiddenInput.setAttribute("value", pk);
    
    console.log('Updating input')

    // Update the non-hidden input to show the selected item's display text
    let widgetDisplayId = widgetName + "_display";
    document.getElementById(widgetDisplayId).value = displayText;

    // Update the view div to show the selected item
    let view_div = document.getElementById(widgetName + "_view_div");
    view_div.querySelector('span').innerHTML = displayText;
}

function removeForeignKey(widgetName) {
    // Get the hidden input
    hiddenInputId = widgetName + "_hidden_input";
    let hiddenInput = document.getElementById(hiddenInputId);

    // Clear the hidden input
    hiddenInput.setAttribute("value", "");

    // Clear the display input
    let widgetDisplayId = widgetName + "_display";
    document.getElementById(widgetDisplayId).value = "";

    // Clear the view div
    let view_div = document.getElementById(widgetName + "_view_div");
    view_div.querySelector('span').innerHTML = "";
}

function makeAdvancedSearchTableClickable(widgetName, widgetType) {
    // Get all of the advanced search divs
    // An advanced search div has the id of widgetName_advanced_search
    let div = document.getElementById(widgetName + '_advanced_search_table');
    
    let listViewFilterDivList = document.querySelectorAll('[id^="list_view_filter"]');

    listViewFilterDivList.forEach(listViewFilterDiv => {
        listViewFilterDiv.addEventListener('click', function(event) {
            event.stopPropagation();
        }
    )});

    // Get the table from the div
    let table = div.querySelector('.table');

    if (table == null) {
        // If the table doesn't exist, return
        return;
    }

    // Add event listener to the rows
    let rows = table.querySelectorAll('tr');
    rows.forEach(row => {
        row.addEventListener('click', function() {
            let pk = row.getAttribute('data-id');
            let displayText = row.getAttribute('data-display-text');
            
            if (widgetType == 'm2m') {
                setM2MValue(pk, displayText, widgetName);
            } else if (widgetType == 'fk') {
                setForeignKeyValue(pk, displayText, widgetName);
            }

            // Close the modal
            let modalId = document.getElementById(`advancedSearchModal${widgetName}`);
            let modal = bootstrap.Modal.getInstance(modalId);
            modal.hide();
        });
    });

    // Function that toggles the working of the forms within the listViewFilterDiv to avoid conflict with nested forms


}