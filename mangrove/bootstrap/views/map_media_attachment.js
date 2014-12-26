function (doc) {
    if (doc.document_type == "Media_Document") {
        if(doc.size > 0) emit(doc.questionnaire_id, 1);
    }
}