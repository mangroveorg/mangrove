import datetime
from mangrove.datastore.database import get_db_manager, \
    _delete_db_and_remove_db_manager
from mangrove.datastore.views import find_views
from pytz import UTC
import random
from mangrove.datastore.entity import Entity
from mangrove.datastore.datadict import DataDictType
from collections import defaultdict


class ViewGenerationTimer(object):

    def _set_db_manager(self):
        self.manager = get_db_manager('http://localhost:5984/',
                                      'mangrove-test')

    def _delete_db_and_remove_db_manager(self):
        _delete_db_and_remove_db_manager(self.manager)

    def _refresh_db_manager(self):
        self._set_db_manager()
        self._delete_db_and_remove_db_manager()
        self._set_db_manager()

    def _reset(self, number_of_entities=0, number_of_data_records_per_entity=8):
        self._number_of_entities = number_of_entities
        self._refresh_db_manager()
        self._setup_entities()
        self._setup_datadict_types()
        self._add_data_to_entities(number_of_data_records_per_entity)

    def _setup_entities(self):
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        AGGREGATION_PATH_NAME = "governance"

        # Entities for State 1: Maharashtra
        # location, aggregation_path
        locations = [
            ['India', 'MH', 'Pune'],
            ['India', 'MH', 'Mumbai'],
            ['India', 'Karnataka', 'Bangalore'],
            ['India', 'Karnataka', 'Hubli'],
            ['India', 'Kerala', 'Kochi'],
            ]
        aggregation_paths = [
            ["Director", "Med_Supervisor", "Surgeon"],
            ["Director", "Med_Supervisor", "Nurse"],
            ["Director", "Med_Officer", "Doctor"],
            ["Director", "Med_Officer", "Surgeon"],
            ["Director", "Med_Officer", "Nurse"],
            ]

        self.entities = []
        for i in range(self._number_of_entities):
            location = random.choice(locations)
            aggregation_path = random.choice(aggregation_paths)
            e = Entity(self.manager, entity_type=ENTITY_TYPE, location=location)
            e.set_aggregation_path(AGGREGATION_PATH_NAME, aggregation_path)
            e.save()
            self.entities.append(e)

    def _setup_datadict_types(self):
        # name=slug, primitive_type
        data_dict_types = [
            ['beds', 'number'],
            ['meds', 'number'],
            ['patients', 'number'],
            ['doctors', 'number'],
        ]
        self.dd_types = {}
        for data_dict_type in data_dict_types:
            name_slug = data_dict_type[0]
            kwargs = {
                'dbm': self.manager,
                'name': name_slug,
                'slug': name_slug,
                'primitive_type': data_dict_type[1],
                }
            self.dd_types[name_slug] = DataDictType(**kwargs)
            self.dd_types[name_slug].save()

    def _add_data_to_entities(self, number_of_data_records_per_entity):
        months = [1]
        number_of_years = number_of_data_records_per_entity / (
            len(self.dd_types) * len(months)
            )
        years = range(2011 - max(1, number_of_years), 2011)
        event_times = []
        for year in years:
            for month in months:
                event_time = datetime.datetime(year, month, 1, tzinfo=UTC)
                event_times.append(event_time)

        for e in self.entities:
            for dd_type in self.dd_types.values():
                for event_time in event_times:
                    slug = dd_type.slug
                    value = random.random()
                    e.add_data(
                        data=[(slug, value, self.dd_types[slug])],
                        event_time=event_time
                        )

    def print_csv_of_view_generation_times(self):
        iterations = [20, 40, 60, 80, 100]
        times_by_view_name = defaultdict(dict)
        for number_of_entities in iterations:
            times = self._calculate_view_generation_time(number_of_entities, 8)
            for k, v in times.items():
                times_by_view_name[k][number_of_entities] = str(v)
        print ",".join(["number of entities"] + [str(i) for i in iterations])
        for name, times in times_by_view_name.items():
            row = [name] + [times_by_view_name[name][number_of_entities] for number_of_entities in iterations]
            print ",".join(row)

    def print_view_generation_times(self):
        times = self._calculate_view_generation_time(100, 8)
        import operator
        sorted_times = sorted(times.iteritems(), key=operator.itemgetter(1))
        for view_name, generation_time in sorted_times:
            print view_name + ": " + str(generation_time)

    def _calculate_view_generation_time(self, number_of_entities, number_of_data_records_per_entity):
        self._reset(number_of_entities, number_of_data_records_per_entity)

        js_views = find_views()
        times = {}
        for v in js_views.keys():
            funcs = js_views[v]
            js_map = (funcs['map'] if 'map' in funcs else None)
            js_reduce = (funcs['reduce'] if 'reduce' in funcs else None)
            start = datetime.datetime.now()
            self.manager.create_view(v, js_map, js_reduce, view_document=v)
            all_rows = self.manager.load_all_rows_in_view(v + "/" + v)
            # we need to hit the view to make sure it compiles
            number_of_rows = len(all_rows)
            end = datetime.datetime.now()
            times[v] = (end - start).total_seconds()
        return times


if __name__ == "__main__":
    divider = "-" * 70
    timer = ViewGenerationTimer()
    print divider
    timer.print_view_generation_times()
    print divider
    timer.print_csv_of_view_generation_times()
    print divider
