function(doc) {
  if (doc.document_type == 'Questionnaire') {
      emit(doc.short_id, doc);
  }
}
