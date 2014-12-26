function (doc) {
    if (doc.document_type == "MediaDetails") {
        if(doc.size > 0) emit(doc.questionnaire_id, 1);
    }
}