function(doc) {
  if (!doc.void) {
    for (k in doc.data){
      value = {};
      var date = Date.parse(doc.event_time);
      key = [doc.entity_backing_field.aggregation_paths['_type'],
             doc.entity_backing_field._id,k, date];
      value["timestamp"] = date;
      value["type"] = doc.data[k]['type']['primitive_type'];
      value["value"] = doc.data[k].value;
      value["field"] = k;
      value["entity_id"] = doc.entity_backing_field._id;
      value["location"] = doc.entity_backing_field.aggregation_paths['_geo'];
      emit(key, value);
    }
  }
  
}

