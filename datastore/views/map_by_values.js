function(doc) {
    if (doc.void) { return null; }
      for (k in doc.data){
        value = {};
        var date = new Date(doc.event_time);
        key = [doc.entity_backing_field.aggregation_paths['_type'],
           doc.entity_backing_field._id,k,date.getUTCFullYear(), date.getUTCMonth() + 1,
           date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()];
        value["timestamp"] = date.getTime();
        value["type"] = doc.data[k].type;
        value["value"] = doc.data[k].value;
        value["field"] = k;
        value["entity_id"] = doc.entity_backing_field._id;
        value["location"] = doc.entity_backing_field.aggregation_paths['_geo'];
        emit(key, value);
      }
}
