function(doc) {
    if (doc.document_type == 'Entity') {
        for (var i = 0; i < doc.aggregation_paths['_type'].length; i++) {
            for (var j = 0; j < doc.aggregation_paths['_geo'].length; j++) {
                type_path = [doc.aggregation_paths['_type'][i]];
                geo_path = doc.aggregation_paths['_geo'].slice(0, j + 1);
                emit(type_path.concat(geo_path), 1);
            }
        }
    }
}