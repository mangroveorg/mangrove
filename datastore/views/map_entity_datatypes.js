function(doc) {
  if (doc.document_type == "DataRecord") {
    for (var i = 0; i < doc.data.length; i++) {
      emit(doc.entity_backing_field['_id'], doc.data[i]['type']['_id']);
    }
  }
}