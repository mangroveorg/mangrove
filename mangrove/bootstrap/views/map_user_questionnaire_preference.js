function(doc) {
    if (doc.document_type == 'UserQuestionnairePreference' && !doc.void) {
        emit([doc.user_id, doc.project_id], doc);
    }
}
