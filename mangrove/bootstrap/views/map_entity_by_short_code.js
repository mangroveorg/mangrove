function(doc) {
    if (doc.document_type == 'Entity' || doc.document_type == 'Contact') {
        emit([doc.aggregation_paths['_type'],doc.short_code], null);
    }
}
