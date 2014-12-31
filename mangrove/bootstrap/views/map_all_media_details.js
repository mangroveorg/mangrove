function (doc) {
    if (doc.document_type == "MediaDetails") {
        emit(doc.questionnaire_id, doc.size);
    }
}