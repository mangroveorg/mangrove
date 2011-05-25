function(key, values, rereduce) {
	if (rereduce == false){
		result = {};
		current = values[0];
		total = 0;
		count = 0;
		for(i in values){
			count = count + 1;
			x = values[i];
    			if (x.timestamp > current.timestamp) current = x;
			if (typeof(x.value)=='number') total = total + x.value;
		}
		result.latest = current.value;
		result.timestamp = current.timestamp;
		result.sum = total;
        result.count = count;
        result.location = values[0].location;
		return result;
	}
	else{
        result = {};
		current = values[0];
		total = 0;
		count = 0;
		for(i in values){
			x = values[i];
			count = count + x.count;
    			if (x.timestamp > current.timestamp) current = x;
			if (typeof(x.sum)=='number') total = total + x.sum;
		}
        result.latest = current.value;
        result.timestamp = current.timestamp;
        result.sum = total;
        result.count = count;
        result.location = values[0].location;
        return result;
	}

}