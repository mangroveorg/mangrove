function(doc) {
  if (!doc.void) {
    for (k in doc.data){
      value = {};
      var date = Date.parse(doc.event_time);
      key = [doc.entity_backing_field.aggregation_paths['_type'],
             doc.entity_backing_field._id,k, date];
      value["timestamp"] = date;
      value["value"] = doc.data[k].value;
      emit(key, value);
    }
  }
  
}

