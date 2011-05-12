function(doc) {
  if (doc.document_type == 'Entity') {
    for (index in doc.aggregation_paths._type) {
      emit(doc.aggregation_paths._type[index], 1);
    }
  }
}
