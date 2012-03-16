function(doc) {
    if (doc.document_type == "Entity") {
        emit(doc.aggregation_paths['_type'], 1);
    }
}