function (doc) {
    if (doc.document_type == "MediaDetails" && !doc.is_preview) {
        if(doc.size > 0) emit(doc.questionnaire_id, 1);
    }
}