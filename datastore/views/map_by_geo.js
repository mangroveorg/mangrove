function(doc) {
    if (doc.document_type == 'Entity') {
        for (var i = 0; i < doc.aggregation_paths['_geo'].length; i++) {
            emit(doc.aggregation_paths['_geo'].slice(0, i + 1), 1);
        }
    }
}
