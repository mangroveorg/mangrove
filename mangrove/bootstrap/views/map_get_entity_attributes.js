function(doc) {
    if (doc.document_type == "Entity") {
        var entity_type = doc.aggregation_paths['_type'];
        var entity_id = doc.short_code;
        value = {};
        for (k in doc.data) {
            key = [entity_type,entity_id];
            value[k] = doc.data[k].value;
        }
        emit(key, value);
    }
}
