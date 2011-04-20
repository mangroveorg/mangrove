function(key, values, rereduce) {
	if (rereduce == false){
		final = {};
		for(i in values){
                    f = values[i].field;
                    if (final[f] === undefined){
                       final[f] = {};
                       result = final[f];
                       result.entity_id = values[i].entity_id;
                       result.field = values[i].field;
                       result.location = values[i].location;
                       result.count = 0;
                       result.timestamp = values[i].timestamp;
                       result.latest = values[i].value;
                       result.sum = 0;
                    }
                    result = final[f];
                    result.count = result.count + 1;
                    if (values[i].timestamp > result.timestamp) {
                            result.timestamp = values[i].timestamp;
                            result.latest = values[i].value;
                    }
                    if (typeof(value[i].value)=='number') result.sum = result.sum + values[i].value;
                }
		return final;
	}
	else{
        final = {};
		for(i in values){
               field_dict = values[i];
               for (k in field_dict){
                    f = k;
                    value = field_dict[k];
                    if (final[f] === undefined){
                        final[f] = {};
                        result = final[f];
                        result.entity_id = value.entity_id;
                        result.field = value.field;
                        result.location = value.location;
                        result.count = 0;
                        result.timestamp = value.timestamp;
                        result.latest = value.latest;
                        result.sum = 0;

                    }
                    result = final[f];
                    result.count = result.count + value.count;
                    if (value.timestamp > result.timestamp) {
                        result.timestamp = value.timestamp;
                        result.latest = value.latest;
                    }
                if (typeof(value.sum)=='number') result.sum = result.sum + value.sum;
                }
		}
        return final;
	}
}
