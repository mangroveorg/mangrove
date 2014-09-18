function(doc) {
    if (doc.document_type == 'SurveyResponse') {
        emit([doc.form_model_id, Date.parse(doc.created) ], doc);
    }
}