class AttributeDict(dict):
    """Simple utility to allow accessing dict members as attributes."""

    def __getattr__(self, attr):
        val = self.get(attr, None)
        if isinstance(val, dict):
            return AttributeDict(val)
        elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            return [AttributeDict(x) for x in val]
        else:
            return val

    def __setattr__(self, attr, value):
        self[attr] = value
