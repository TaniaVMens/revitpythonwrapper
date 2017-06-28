"""
Wall Wrappers

"""  #

import rpw
from rpw import revit, DB
from rpw.db import Element
from rpw.db import FamilyInstance, FamilySymbol, Family, Category
from rpw.base import BaseObjectWrapper
from rpw.utils.logger import logger
from rpw.db.builtins import BipEnum


class Wall(FamilyInstance):
    """
    Inherits base ``Instance`` and overrides symbol attribute to
    get `Symbol` equivalent of Wall - WallType `(GetTypeId)`
    """

    _revit_object_category = DB.BuiltInCategory.OST_Walls
    _revit_object_class = DB.Wall
    _collector_params = {'of_class': _revit_object_class, 'is_type': False}

    @property
    def symbol(self):
        return self.wall_type

    @property
    def wall_type(self):
        wall_type_id = self._revit_object.GetTypeId()
        wall_type = self.doc.GetElement(wall_type_id)
        return WallType(wall_type)

    @property
    def wall_kind(self):
        return self.wall_type.wall_kind

    @property
    def family(self):
        return self.wall_kind


class WallType(FamilySymbol):
    """
    Inherits from :any:`Symbol` and overrides:
        * :func:`wall_kind` to get the `Family` equivalent of Wall `(.Kind)`
        * Uses a different method to get instances.
    """

    _revit_object_class = DB.WallType
    _collector_params = {'of_class': _revit_object_class, 'is_type': True}


    @property
    def family(self):
        return self.wall_kind

    @property
    def wall_kind(self):
        """ Returns ``DB.Family`` of the Symbol """
        return WallKind(self._revit_object.Kind)

    @property
    def instances(self):
        """ Returns all Instances of this Wall Types """
        bip = BipEnum.get_id('SYMBOL_NAME_PARAM')
        param_filter = rpw.db.ParameterFilter(bip, equals=self.name)
        return rpw.db.Collector(parameter_filter=param_filter,
                                **Wall._collector_params).wrapped_elements

    @property
    def siblings(self):
        return self.wall_kind.wall_types


# class WallKind(Family):
class WallKind(BaseObjectWrapper):
    """
    Equivalent of ``Family`` but is Enumerator for Walls.

    Can be Basic, Stacked, Curtain, Unknown
    """

    _revit_object_class = DB.WallKind

    @property
    def name(self):
        # Same method as Family Works, but requires Code duplication
        # Since this should not inherit from Family.
        # Solution copy code or Mixin. Returning just Enum Name for now
        # 'Basic'
        return self._revit_object.ToString()

    @property
    def symbols(self):
        return self.wall_types

    @property
    def wall_types(self):
        wall_types = rpw.db.Collector(**WallType._collector_params).wrapped_elements
        return [wall_type for wall_type in wall_types
                if wall_type.Kind == self._revit_object]

    @property
    def instances(self):
        """ Returns all Wall instances of this given Wall Kind"""
        instances = []
        for wall_type in self.wall_types:
            instances.extend(wall_type.instances)
        return instances

    @property
    def category(self):
        wall_type = rpw.db.Collector(of_class=DB.WallType, is_type=True).first
        return WallCategory(wall_type.Category)


class WallCategory(Category):
    """
    ``DB.Category`` Wall Category Wrapper

    Attribute:
        _revit_object (DB.Family): Wrapped ``DB.Category``
    """

    _revit_object_class = DB.Category

    @property
    def families(self):
        """ Returns ``DB.WallKind`` elements in the category """
        wall_kinds = []
        for member in dir(DB.WallKind):
            if type(getattr(DB.WallKind, member)) is DB.WallKind:
                wall_kinds.append(getattr(DB.WallKind, member))
        return wall_kinds
