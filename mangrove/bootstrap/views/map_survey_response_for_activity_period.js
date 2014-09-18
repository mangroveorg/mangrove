function(doc) {
    if (doc.document_type == 'SurveyResponse' && !doc.void) {
        emit([doc.form_model_id, Date.parse(doc.event_time) ], doc);
    }
}