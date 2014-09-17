function(doc) {
    var isNotNull = function(o) {
        return !((o === undefined) || (o == null));
    };
    if (doc.document_type == 'SurveyResponse' && isNotNull(doc.form_model_id)) {
        emit([doc.form_model_id, Date.parse(doc.created) ], doc);
    }
}