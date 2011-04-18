function(key, values, rereduce) {
    if (rereduce == false) {
        result = {};
        current = values[0];
        total = 0;
        count = 0;
        for (i in values) {
            count = count + 1;
            x = values[i];
            if (x.timestamp > current.timestamp) current = x;
            total = total + x.value;
        }
        result.latest = current.value;
        result.timestamp = current.timestamp;
        result.sum = total;
        result.count = count;
        result.entity_id = values[0].entity_id;
        result.field = values[0].field;
        result.aggregation_paths = values[0].aggregation_paths;
        return result;
    }
    else {
        result = {};
        current = values[0];
        total = 0;
        count = 0;
        for (i in values) {
            x = values[i];
            count = count + x.count;
            if (x.timestamp > current.timestamp) current = x;
            total = total + x.sum;
        }
        result.latest = current.value;
        result.timestamp = current.timestamp;
        result.sum = total;
        result.count = count;
        result.entity_id = values[0].entity_id;
        result.field = values[0].field;
        result.aggregation_paths = values[0].aggregation_paths;
        return result;

    }

}