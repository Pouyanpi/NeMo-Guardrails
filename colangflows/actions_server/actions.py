# A decorator that sets a property on the class to indicate if it's a action or not.
def action(cls):
    cls.is_action = True
    return cls
