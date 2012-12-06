function(doc) {
    if (doc.document_type == "Entity" && !doc.void && doc.aggregation_paths['_type'][0] != 'reporter') {
        emit(doc.aggregation_paths['_type'], doc);
    }
}