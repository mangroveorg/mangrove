function(doc) {
    if (!doc.void && doc.document_type == "DataRecord")
    {
        entity_type = doc.entity.aggregation_paths['_type'];
        var date = new Date(doc.event_time);
        for (f in doc.data) {
	    value = {};
            value["timestamp"] = date;
            value["value"] = doc.data[f].value;
            k = [date.getUTCFullYear(),date.getUTCMonth() + 1,date.getDate(),doc.submission.form_code,entity_type,
doc.entity.short_code,f];
            emit(k, value);
        }
    }
}