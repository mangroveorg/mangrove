function(doc) {
  if (doc.document_type == 'DataRecord') {
    if (doc.void) { return null; }
    for (var label in doc.data) {
      var value = doc.data[label]['value'];
      var entity_id = doc.entity_backing_field['_id'];
      emit([label, value], entity_id);
    }
  }
}