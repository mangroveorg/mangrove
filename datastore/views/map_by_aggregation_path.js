function(doc) {
    if (!doc.void && doc.document_type == "DataRecord")
    {
        entity_type = doc.entity.aggregation_paths['_type'];
        var date = new Date(doc.event_time);
        dates = [date.getUTCFullYear(), date.getUTCMonth() + 1,
                date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()];
        for (f in doc.data) {
	        value = doc.data[f].value;
	        if (typeof(value)=='number'){
             for (p in doc.entity.aggregation_paths) {
                k = [entity_type,p,f];
                k = k.concat(doc.entity.aggregation_paths[p]);
                k = k.concat(dates);
                emit(k, value);
                }
	        }
        }
    }
}
