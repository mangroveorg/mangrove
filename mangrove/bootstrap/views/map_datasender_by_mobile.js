function(doc) {
    if (doc.document_type == "Contact" && doc.aggregation_paths._type[0] == 'reporter' && !doc.void) {
        var data = doc.data;
        emit([data.mobile_number.value, doc.short_code], null);
    }
}