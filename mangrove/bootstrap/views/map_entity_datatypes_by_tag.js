function(doc) {
    if (doc.document_type == "DataRecord") {
        for (var i in doc.data) {
            for (var j in doc.data[i]['type']['tags']) {
                emit([doc.entity['_id'], doc.data[i]['type']['tags'][j]], doc.data[i]['type']['_id']);
            }
        }
    }
}