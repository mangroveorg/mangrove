class ConstraintAttributes(object):
    MAX="max"
    MIN="min"

class IntegerConstraint(object):

    def __init__(self,min=None,max=None):
        self.min=min
        self.max=max

    def _to_json(self):
        dict={}
        if self.min is not None:
            dict[ConstraintAttributes.MIN] = self.min
        if self.max is not None:
            dict[ConstraintAttributes.MAX] = self.max
        return dict




         