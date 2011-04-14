function(doc) {
    if (doc.void) { return null; }
    var isNumeric = function(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    };
    var isNotNull = function(o) {
        return !((o === undefined) || (o == null));
    };
    if (doc.document_type == 'DataRecord' && isNotNull(doc.entity_backing_field)) {
        var value = {};
        var date = new Date(doc.event_time);
        for (index in doc.data) {
            if (isNotNull(doc.data[index]) && isNotNull(doc.data[index].value) && isNumeric(doc.data[index].value)) {
                value[index] = parseFloat(doc.data[index].value);
            }
        }
        for (index in value) {
            var key = [doc.entity_backing_field.aggregation_paths['_type'], index, date.getUTCFullYear(),
                       date.getUTCMonth() + 1, date.getUTCDate(), date.getUTCHours(),
                       date.getUTCMinutes(), date.getUTCSeconds()];
            emit(key, value[index]);
        }
    }
}