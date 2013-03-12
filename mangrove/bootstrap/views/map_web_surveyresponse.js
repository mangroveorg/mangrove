function(doc) {
    var isNotNull = function(o) {
        return !((o === undefined) || (o == null));
    };
    if (doc.document_type == 'SurveyResponse' && isNotNull(doc.form_code) && doc.channel=='web') {
        emit([doc.form_code, Date.parse(doc.created) ], doc);
    }
}