function(doc) {
    if (doc.document_type == 'SurveyResponse') {
        emit(doc._id,doc);
    }
}