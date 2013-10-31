function(doc) {
    if (doc.document_type == "Entity" && doc.aggregation_paths._type[0] == 'reporter') {
        var data = doc.data;
        if (data.email){
            emit(data.email.value, doc);
        }
    }
}