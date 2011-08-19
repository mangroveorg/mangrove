function(doc) {
  if (doc.document_type == 'Entity' && doc.aggregation_paths['_type'][0] == 'reporter') {
      emit(doc.short_code, null);
  }
}