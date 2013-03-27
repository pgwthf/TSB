from __future__ import division
from __future__ import absolute_import

#from django.db import models
#
#try:
#        import cPickle as pickle
#except ImportError:
#        import pickle
#
#
#class DictField(models.CharField):
#
#    description = "Stores a standard Python dictionary in a CharField"
#
#    __metaclass__ = models.SubfieldBase
#
#
#    def __init__(self, *args, **kwargs):
#        kwargs['max_length'] = 250 #is this given by the function??
#        super(DictField, self).__init__(*args, **kwargs)
#
#
#    def to_python(self, value):
#        if isinstance(value, dict):
#            return value
#        else:
#            try:
#                return pickle.loads(str(value))
#            except:
#                return value
#
#
#    def get_prep_value(self, value):
#            if isinstance(value, dict):
#                return pickle.dumps(value)
#            else:
#                raise TypeError('This field can only store dictionaries.')
#
#
#    def get_prep_lookup(self, lookup_type, value):
#        if lookup_type == 'exact':
#            return self.get_prep_value(value)
#        elif lookup_type == 'in':
#            return [self.get_prep_value(v) for v in value]
#        else:
#            raise TypeError('Lookup type {} is not supported.'.format(
#                                                                lookup_type))
