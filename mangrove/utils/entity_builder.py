from mangrove.datastore.entity import create_entity, get_by_short_code, create_contact
from mangrove.datastore.entity_type import entity_type_already_defined, define_type
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.form_model.form_model import REPORTER


class EntityBuilder(object):
    def __init__(self, manager, entity_type, short_code):
        self._manager = manager
        self._entity_type = entity_type
        self._short_code = short_code
        self._geometry, self._aggregation_paths, self._location = [None]*3
        self._data = []

    def aggregation_paths(self, aggregation_paths):
        self._aggregation_paths = aggregation_paths
        return self

    def geometry(self, geometry):
        self._geometry = geometry
        return self

    def location(self, location):
        self._location = location
        return self

    def add_data(self,data):
        self._data.append(data)
        return self

    def build(self):
        if not entity_type_already_defined(self._manager, self._entity_type):
            define_type(self._manager, self._entity_type)

        entity = self.create_or_update_entity(self._manager, entity_type=self._entity_type, short_code=self._short_code,
            aggregation_paths=self._aggregation_paths, location=self._location, geometry=self._geometry)
        for each in self._data: entity.add_data(each)
        return entity

    def create_or_update_entity(self, manager, entity_type, location, aggregation_paths, short_code, geometry=None):
        try:
            entity = get_by_short_code(manager, short_code, entity_type)
            entity.delete()
        except DataObjectNotFound:
            pass
        if entity_type == [REPORTER]:
            return create_contact(manager, short_code, location, aggregation_paths, geometry)
        return create_entity(manager, entity_type, short_code, location, aggregation_paths, geometry)
