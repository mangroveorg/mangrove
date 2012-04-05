function(doc) {
    if (doc.document_type == "Entity" && !doc.void) {
        emit(doc.aggregation_paths['_type'], 1);
    }
}