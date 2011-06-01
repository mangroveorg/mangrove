function(key, values, rereduce) {
    result = {};
    current = values[0];
    if (rereduce == false){
        for(i in values){
            x = values[i];
                if (x.timestamp > current.timestamp) current = x;
        }
        result.latest = current.value;
        result.timestamp = current.timestamp;
        result.short_code = current.short_code;
        return result;
    }
    else{
        for(i in values){
            x = values[i];
                if (x.timestamp > current.timestamp) current = x;
        }
        result.latest = current.latest;
        result.timestamp = current.timestamp;
        result.short_code = current.short_code;
        return result;
    }
}