function(doc) {
    if (doc.document_type == 'DataRecord') {
        for (var label in doc.data) {
            var id = doc.data[label]['type']['_id'];
            emit([id, label], null);
        }
    }
}