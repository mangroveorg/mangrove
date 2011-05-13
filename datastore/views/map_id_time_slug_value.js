function(doc) {
  if (doc.document_type == "DataRecord") {
    for (var i in doc.data) {
      var entity_id = doc.entity_backing_field['_id'];
      var result = {
        'event_time': doc.event_time,
        'slug': doc.data[i]['type']['slug'],
        'value': doc.data[i]['value']
      };
      emit(entity_id, result);
    }
  }
}
