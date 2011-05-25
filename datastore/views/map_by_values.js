function(doc) {
  if (!doc.void) {
    for (k in doc.data){
        value = doc.data[k].value;
        if (typeof(value)=='number') {
            var date = Date.parse(doc.event_time);
            key = [doc.entity_backing_field.aggregation_paths['_type'],
             doc.entity_backing_field._id,k, date];
            emit(key, value);
      }
    }
  }
}

