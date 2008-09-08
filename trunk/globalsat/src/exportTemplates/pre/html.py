def pre(track):    
    threshold = .00001
    num_levels = 4
    zoom_factor = 32
    zoom_level_breaks = []
    for i in range(num_levels):
        zoom_level_breaks.append(threshold * (zoom_factor ** (num_levels - i - 1)))
        
    def encode_pairs(points):
        encoded_points = []
        encoded_levels = []
        
        distances = douglas_peucker_distances(points)
        points_of_interest = []
        for i, d in enumerate(distances):
            if d is not None:
                lat, long = points[i]
                points_of_interest.append((lat, long, d))
        
        lat_prev, long_prev = 0, 0
        for lat, long, d in points_of_interest:
            encoded_lat, lat_prev = encode_lat_or_long(lat, lat_prev)
            encoded_long, long_prev = encode_lat_or_long(long, long_prev)
            encoded_points += [encoded_lat, encoded_long]
            encoded_level = encode_unsigned(num_levels - compute_level(d) - 1)
            encoded_levels.append(encoded_level)
    
        encoded_points_str = ''.join(encoded_points).replace(chr(92),chr(92)+chr(92))
        encoded_levels_str = ''.join([str(l) for l in encoded_levels])
        return encoded_points_str, encoded_levels_str
    
    def encode_lat_or_long(x, prev_int):
        int_value = int(float(x) * 1e5)
        delta = int_value - prev_int
        return encode_signed(delta), int_value
    
    def encode_signed(n):
        tmp = n << 1
        if n < 0:
            tmp = ~tmp
        return encode_unsigned(tmp)
    
    def encode_unsigned(n):
        tmp = []
        # while there are more than 5 bits left (that aren't all 0)...
        while n >= 32:  # 32 == 0xf0 == 100000
            tmp.append(n & 31)  # 31 == 0x1f == 11111
            n = n >> 5
        tmp = [(c | 0x20) for c in tmp]
        tmp.append(n)
        tmp = [(i + 63) for i in tmp]
        tmp = [chr(i) for i in tmp]
        tmp = ''.join(tmp)
        return tmp    
    
    def douglas_peucker_distances(points):
        distances = [None] * len(points)
        distances[0] = threshold * (zoom_factor ** num_levels)
        distances[-1] = distances[0]
    
        if(len(points) < 3):
            return distances
    
        stack = [(0, len(points) - 1)]
        while stack:
            a, b = stack.pop()
            max_dist = 0
            for i in range(a + 1, b):
                dist = distance(points[i], points[a], points[b])
                if dist > max_dist:
                    max_dist = dist
                    max_i = i
            if max_dist > threshold:
                distances[max_i] = max_dist
                stack += [(a, max_i), (max_i, b)]
    
        return distances
    
    def distance(point, A, B):
        """Compute distance of ``point`` from line ``A``, ``B``."""
        if A == B:
            out = math.sqrt(
                (B[0] - point[0]) ** 2 +
                (B[1] - point[1]) ** 2
            )
        else:
            u = (
                (((point[0] - A[0]) * (B[0] - A[0])) +
                 ((point[1] - A[1]) * (B[1] - A[1]))) / 
                (((B[0] - A[0]) ** 2) +  ((B[1] - A[1]) ** 2))
            )
            if u <= 0:
                out = math.sqrt(
                    ((point[0] - A[0]) ** 2) + ((point[1] - A[1]) ** 2)
                )
            elif u >= 1:
                out = math.sqrt(
                    ((point[0] - B[0]) ** 2) + ((point[1] - B[1]) ** 2)
                )
            elif 0 < u < 1:
                out = math.sqrt(
                    ((((point[0] - A[0]) - (u * (B[0] - A[0]))) ** 2)) +
                    ((((point[1] - A[1]) - (u * (B[1] - A[1]))) ** 2))
                )
        return out
    
    def compute_level(distance):
        """Compute the appropriate zoom level of a point in terms of its 
        distance from the relevant segment in the DP algorithm."""
        if distance > threshold:
            level = 0
        while distance < zoom_level_breaks[level]:
            level += 1
        return level
    
    
    #main execution
    pairs = list()
    for trackpoint in track.trackpoints:
        pairs.append((trackpoint.latitude, trackpoint.longitude))    
    
    track.encodedPoints, track.encodedLevels = encode_pairs(pairs)