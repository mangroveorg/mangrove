function(key, values, rereduce) {
    result = {};
    if (rereduce == false) {
        result.count = values.length;
        result.success = 0;
        for (i in values) {
            x = values[i];
            if (x.status) result.success += 1;
        }
        return result;
    }
    else {
        result.count = 0;
        result.success = 0;
        for (i in values) {
            x = values[i];
            result.count += x.count;
            result.success += x.success;
        }
        return result;
    }
}
