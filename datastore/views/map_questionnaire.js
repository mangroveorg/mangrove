function(doc) {
  if (doc.document_type == 'Questionnaire') {
      emit(doc.questionnaire_code, doc);
  }
}
