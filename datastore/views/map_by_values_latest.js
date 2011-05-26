function(doc) {
  if (!doc.void && doc.document_type == "DataRecord") {
    var date = Date.parse(doc.event_time);
    var entity = doc.entity_backing_field;
    var entity_type = entity.aggregation_paths['_type'];
    var entity_id = entity._id;
    for (k in doc.data){
      value = {};
      key = [entity_type,entity_id,k, date];
      value["timestamp"] = date;
      value["value"] = doc.data[k].value;
      emit(key, value);
    }
  }
}

