function(doc) {
    if (!doc.void && doc.document_type == "DataRecord")
    {
        entity_type = doc.entity_backing_field.aggregation_paths['_type'];
        for (f in doc.data) {
	        value = doc.data[f].value;
	        if (typeof(value)=='number'){
             var date = new Date(doc.event_time);
             key = [date.getUTCFullYear(), date.getUTCMonth() + 1,
                date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()];
             for (p in doc.entity_backing_field.aggregation_paths) {
                k = [entity_type];
                k.push(p);
                k.push(f);
                k = k.concat(doc.entity_backing_field.aggregation_paths[p]);
                k = k.concat(key);
                emit(k, value);
                }
	        }
        }
    }
}
