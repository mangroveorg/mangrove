function(doc) {
    if ((doc.document_type == "Entity" || doc.document_type == "Contact") && !doc.void) {
        emit([doc.aggregation_paths['_type'],doc.short_code], null);
    }
}