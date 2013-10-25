INVALID_VALUE = 'INVALID_VALUE'

def access_data_by_path(data, path):
    segments = _parse_path(path)
    v,e = _get(data, segments)
    if v == INVALID_VALUE or (e and len(v) == 0):
        raise KeyError(path)
    return v

def _parse_path(path):
    segments = []
    if not isinstance(path, (list,tuple)):
        path = [path]
    for k in path:
        if isinstance(k, basestring):
            segments.extend(k.split('/'))
        else:
            segments.append(k)
    if len(segments) == 0:
        raise IndexError()
    segments.reverse()
    return segments

# returns two parameters: the first is a value, or a list of values; and the
# second indicates whether the first returned parameter is a list that was
# expanded from a '*', or not
def _get(o, segments):
    if len(segments) == 0:
        return (o,False)
    s = segments.pop()

    if isinstance(s,basestring):
        if s == '' and len(segments) == 0:
            return (o,False)
        elif s == '*':
            items = []
            if isinstance(o, dict):
                items = o.itervalues()
            elif hasattr(o, '__iter__'):
                items = iter(o)
            else:
                return (INVALID_VALUE,False)
            n = []
            for i in items:
                v,e = _get(i, segments[:])
                if v is INVALID_VALUE:
                    continue
                if e:
                    n.extend(v)
                else:
                    n.append(v)
            return (n,True)
        elif s.isdigit():
            s = int(s)

    if hasattr(o, '__getitem__'):
        try:
            return _get(o[s], segments)
        except (KeyError,IndexError,TypeError):
            return (INVALID_VALUE,False)
    else:
        return (INVALID_VALUE,False)
