function(doc) {
  if (doc.document_type == 'DataRecord') {
    if (doc.void) { return null; }
    for (var label in doc.data) {
      var type_slug = doc.data[label]['type']['slug'];
      var value = doc.data[label]['value'];
      var entity_id = doc.entity_backing_field['_id'];
      emit([label, type_slug, value], entity_id);
    }
  }
}