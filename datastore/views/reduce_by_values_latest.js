function(key, values, rereduce) {
    result = {};
    current = values[0];
    for(i in values){
        x = values[i];
            if (x.timestamp > current.timestamp) current = x;
    }
    result.latest = current.value;
    result.timestamp = current.timestamp;
    return result;
}