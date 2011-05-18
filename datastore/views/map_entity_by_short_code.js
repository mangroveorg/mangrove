function(doc) {
  if (doc.document_type == 'Entity') {
      emit(doc.short_code, null);
  }
}
