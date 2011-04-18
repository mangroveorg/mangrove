function(doc) {
    if (doc.void)
    {
        return null;
    }
    entity_type = doc.entity_backing_field.aggregation_paths['_type'];
    for (f in doc.data) {
        value = {};
        var date = new Date(doc.event_time);
        key = [date.getUTCFullYear(), date.getUTCMonth() + 1,
            date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()];
        value["timestamp"] = date.getTime();
        value["type"] = doc.data[f].type;
        value["value"] = doc.data[f].value;
        value["field"] = f;
        value["entity_id"] = doc.entity_backing_field._id;
        value['aggregation_paths'] = doc.entity_backing_field.aggregation_paths;
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
