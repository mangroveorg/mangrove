function(doc) {
    if (doc.document_type == "DataRecord") {
        for (var i in doc.data) {
            emit(doc.entity['_id'], doc.data[i]['type']['_id']);
        }
    }
}