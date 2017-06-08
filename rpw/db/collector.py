"""
>>> levels = rpw.Collector(of_category='OST_Levels', is_no_type=True)

>>> # Traditional
>>> levels = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType()

"""

from rpw.revit import revit, DB
from rpw.utils.dotnet import List
from rpw.base import BaseObjectWrapper, BaseObject
from rpw.exceptions import RPW_Exception, RPW_TypeError
from rpw.db.element import Element
from rpw.db.builtins import BicEnum, BipEnum
from rpw.utils.coerce import to_element_ids
from rpw.utils.logger import logger


class Collector(BaseObjectWrapper):
    """
    Revit FilteredElement Collector Wrapper

    Usage:
        >>> collector = Collector(of_class='View')
        >>> elements = collector.elements

        Multiple Filters:

        >>> collector = Collector(of_class='Wall', is_not_type=True)
        >>> collector = Collector(of_class='ViewSheet', is_not_type=True)
        >>> collector = Collector(of_category='OST_Rooms', level=some_level)
        >>> collector = Collector(symbol=SomeSymbol)
        >>> collector = Collector(parameter_filter=filter_rule)

        Chain results using ``filter`` method:

        >>> collector = Collector(of_category='OST_Walls')
        >>> wall_types = collector.filter(is_type=True)
        >>> wall_types = collector.elements  # Both filters applied

        Use Enumeration member or its name as a string:

        >>> Collector(of_category='OST_Walls')
        >>> Collector(of_category=DB.BuiltInCategory.OST_Walls)
        >>> Collector(of_class=DB.ViewType)
        >>> Collector(of_class='ViewType')

        Search Document, View, or list of elements

        >>> Collector(of_category='OST_Walls') # doc is default
        >>> Collector(view=SomeView, of_category='OST_Walls') # Doc is default
        >>> Collector(doc=SomeLinkedDoc, of_category='OST_Walls')
        >>> Collector(elements=[Element1, Element2,...], of_category='OST_Walls')

    Attributes:
        collector.elements: Returns list of all `collected` elements
        collector.first: Returns first found element, or ``None``
        collector.wrapped_elements: Returns list with all elements wrapped. Elements will be instantiated using :any:`Element.Factory`

    Wrapped Element:
        self._revit_object = ``Revit.DB.FilteredElementCollector``

    """

    def __init__(self, **filters):
        """
        Args:
            **filters (``keyword args``): Scope and filters

        Returns:
            Collector (:any:`Collector`): Collector Instance

        Scope Options:
            * ``view`` `(DB.View)`: View Scope (Optional)
            * ``element_ids`` `([ElementId])`: List of Element Ids to limit Collector Scope
            * ``elements`` `([Element])`: List of Elements to limit Collector Scope

        Warning:
            Only one scope filter should be used per query. If more then one is used,
            only one will be applied, in this order ``view`` > ``elements`` > ``element_ids``

        Filter Options:
            * ``is_not_type`` (``bool``): Same as ``WhereElementIsNotElementType``
            * ``is_type`` (``bool``): Same as ``WhereElementIsElementType``
            * ``of_class`` (``Type``): Same as ``OfClass``. Type can be ``DB.SomeType`` or string: ``DB.Wall`` or ``'Wall'``
            * ``of_category`` (``BuiltInCategory``): Same as ``OfCategory``. Type can be Enum member or String: ``DB.BuiltInCategory.OST_Wall`` or ``OST_Wall``
            * ``is_view_independent`` (``bool``): ``WhereElementIsViewIndependent(True)``
            * ``symbol`` (``DB.ElementId``, ``DB.Element``)`: Element or ElementId of Symbol
            * ``level`` (``DB.Level``, ``DB.ElementId``)`: Level or ElementId of Level
            * ``parameter_filter`` (:any:`ParameterFilter`): Similar to ``ElementParameterFilter`` Class

        """
        # Pick Scope Filter, Default is doc
        # Override standard doc with passed doc
        collector_doc = filters.pop('doc') if 'doc' in filters else revit.doc
        if 'view' in filters:
            view = filters.pop('view')
            view_id = view if isinstance(view, DB.ElementId) else view.Id
            collector = DB.FilteredElementCollector(collector_doc, view_id)
        elif 'elements' in filters:
            elements = filters.pop('elements')
            element_ids = to_element_ids(elements)
            collector = DB.FilteredElementCollector(collector_doc, List[DB.ElementId](element_ids))
        elif 'element_ids' in filters:
            element_ids = filters.pop('element_ids')
            collector = DB.FilteredElementCollector(collector_doc, List[DB.ElementId](element_ids))
        else:
            collector = DB.FilteredElementCollector(collector_doc)

        super(Collector, self).__init__(collector)

        self._collector_doc = collector_doc
        self.elements = []

        for key in filters.keys():
            if key not in _Filter.MAP:
                raise RPW_Exception('Collector Filter not valid: {}'.format(key))

        # Stores filters for chained calls
        self._filters = filters

        # Instantiates Filter class on attribute filter
        self.filter = _Filter(self)

        # Allows Class to Excecute on Construction, if filters are present.
        if filters:
            self.filter(**filters)  # Call


    def __iter__(self):
        """ Collector Iterator
        >> for wall in Collector(of_class='Wall'):
        >>     wall
        """
        for element in self._revit_object:
            yield element

    @property
    def first(self):
        """ Returns the first element in collector, or None"""
        try:
            return self.elements[0]
        except IndexError:
            return None

    #TODO: add __iter__

    @property
    def wrapped_elements(self):
        """ Returns list with all elements instantiated using :any:`Element.Factory`
        """
        return [Element.Factory(el) for el in self.elements]

    def __bool__(self):
        """ Evaluates to `True` if Collector.elements is not empty [] """
        return bool(self.elements)

    def __len__(self):
        """ Returns length of collector.elements """
        return len(self.elements)

    def __repr__(self):
        return super(Collector, self).__repr__(data=len(self))


class _Filter(BaseObject):
    """ Filter for Collector class.
    Not to be confused with the Filter Class.
    """
    MAP = {
             'of_class': 'OfClass',
             'of_category': 'OfCategory',
             'is_not_type': 'WhereElementIsNotElementType',
             'is_type': 'WhereElementIsElementType',
             'is_view_independent': 'WhereElementIsViewIndependent',
             'symbol': 'WherePasses',
             'level': 'WherePasses',
             'not_level': 'WherePasses',
             'parameter_filter': 'WherePasses',
            }

    def __init__(self, collector):
        self._collector = collector

    def __call__(self, **filters):
        """
        collector = Collector().filter > ._Filter(filters)
        filters = {'of_class'=Wall}
        """
        filters = self._coerce_filter_values(filters)

        for key, value in filters.iteritems():
            self._collector._filters[key] = value

        filtered_collector = self._chain(self._collector._filters)
        # TODO: This should return iterator to save memory
        self._collector.elements = [element for element in filtered_collector]
        return self._collector

    # TODO: Quick Filters should be run first, then Slow Filters
    def _chain(self, filters, collector=None):
        """ Chain filters together.

        Builts API syntax, by converting ```collector.filter(of_class=X, is_not_type=True)``
        into: ```FilteredElementCollector.OfClass(X).WhereElementisNotElementType()``

        Iteration happens over a copy of filter dictionary, so applied filter
        can be poppped before chain enters deeper recursion level.
        """
        #TODO: parameter_filter should accept list so multiple filters can be applied
        # First Loop
        if not collector:
            collector = self._collector._revit_object

        # Stack is track filter chainning queue
        filter_stack = filters.copy()
        for filter_name, filter_value in filters.iteritems():
            collector_filter = getattr(collector, _Filter.MAP[filter_name])

            if filter_name not in _Filter.MAP:
                raise RPW_Exception('collector filter rule does not exist: {}'.format(filter_name))
            elif isinstance(filter_value, bool):
                # Same as WhereIsElementType(bool)
                if filter_value is True:
                    collector_results = collector_filter()
                # This allow is_type=False to set is_not_type=True
                elif filter_value is False and filter_name == 'is_type':
                    collector_filter = getattr(collector, _Filter.MAP['is_not_type'])
                    collector_results = collector_filter()
                # This allow for is_not_type=False to set is_type=True
                elif filter_value is False and filter_name == 'is_not_type':
                    collector_filter = getattr(collector, _Filter.MAP['is_type'])
                    collector_results = collector_filter()
            elif isinstance(filter_value, ParameterFilter):
                # Same as WherePasses(ParameterFilter)
                collector_results = collector_filter(filter_value._revit_object)
            elif filter_name == 'symbol':
                # Same as WherePasses(FamilyInstanceFilter)
                collector_results = collector_filter(_FamilyInstanceFilter(filter_value, doc=self._collector._collector_doc).unwrap())
            elif filter_name in ('level', 'not_level'):
                # Same as WherePasses(ElementLevelFilter)
                reverse = True if filter_name.startswith('not') else False
                collector_results = collector_filter(_ElementLevelFilter(filter_value, reverse=reverse).unwrap())
            elif filter_name == 'of_class' or filter_name == 'of_category':
                # Same as OfCategory(filter_value) and OfClass(filter_value)
                collector_results = collector_filter(filter_value)
            else:
                raise RPW_Exception('unknown parameter filter error: {}:{}'.format(
                                    filter_name, filter_value))
            filter_stack.pop(filter_name)
            collector = self._chain(filter_stack, collector=collector)

        return collector

    def _coerce_filter_values(self, filters):
        """ Allows filter values to be either Enumerate or string

        Usage:
            >>> elements = Collector(of_category=BuiltInCategory.OST_Walls)
            >>> elements = Collector(of_category='OST_Walls')

            >>> elements = Collector(of_class=WallType)
            >>> elements = Collector(of_class='WallType')

        Note:
            String Connversion for ``of_class`` only works for the ``Revit.DB``
            namespace.

        """
        category_name = filters.get('of_category')
        if category_name and isinstance(category_name, str):
            filters['of_category'] = BicEnum.get(category_name)

        class_name = filters.get('of_class')
        if class_name and isinstance(class_name, str):
            filters['of_class'] = getattr(DB, class_name)

        return filters


class _FamilyInstanceFilter(BaseObjectWrapper):
    """
    Used by Collector to provide the ``symbol`` keyword filter.
    It returns a ``DB.FamilyInstanceFilter`` which is then used by the
    ``FilterElementCollector.WherePasses()`` method to filter by symbol type.

    Wrapped Element:
        self._revit_object = ``Revit.DB.FamilyInstanceFilter``

    """
    def __init__(self, symbol_or_id, doc=revit.doc):
        """
        Args:
            symbol_or_id(``DB.FamilySymbol``, ``DB.ElementId``): FamilySymbol or ElementId

        Returns:
            DB.FamilyInstanceFilter: _FamilyInstanceFilter
        """
        if isinstance(symbol_or_id, DB.ElementId):
            symbol_id = symbol_or_id
        elif isinstance(symbol_or_id, DB.FamilySymbol):
            symbol_id = symbol_or_id.Id
        else:
            raise RPW_TypeError('FamilySymbol or FamilySymbol Id', type(symbol_or_id))

        super(_FamilyInstanceFilter, self).__init__(DB.FamilyInstanceFilter(doc, symbol_id))


class _ElementLevelFilter(BaseObjectWrapper):
    """
    Used by Collector to provide the ``level`` keyword filter.
    It returns a ``DB.ElementLevelFilter `` which is then used by the
    ``FilterElementCollector.WherePasses()`` method to filter by symbol type.

    Wrapped Element:
        self._revit_object = ``Revit.DB.ElementLevelFilter``

    """
    def __init__(self, level_or_id, reverse=False):
        """
        Args:
            level_or_id(``DB.Level``, ``DB.ElementId``): Level or ElementId of Level
            reverse(bool): if True, will match all elements not associated to the given level

        Returns:
            DB.ElementLevelFilter: instance of_ElementLevelFilter()
        """
        if isinstance(level_or_id, DB.ElementId):
            level_id = level_or_id
        elif isinstance(level_or_id, DB.Level):
            level_id = level_or_id.Id
        else:
            raise RPW_TypeError('Level or Level Id', type(level_or_id))

        super(_ElementLevelFilter, self).__init__(DB.ElementLevelFilter(level_id, reverse))


class ParameterFilter(BaseObjectWrapper):
    """ Parameter Filter Wrapper.
    Used to build a parameter filter to be used with the Collector.

    Usage:
        >>> param_id = DB.ElemendId(DB.BuiltInParameter.TYPE_NAME)
        >>> parameter_filter = ParameterFilter(param_id, equals='Wall 1')
        >>> collector = Collector(parameter_filter=parameter_filter)

    Returns:
        FilterRule: A filter rule object, depending on arguments.
    """
    # TODO: parameter_filter from object+param name to skip having to get param_id
    #       basically an alternative constructor that takes elemement + parameter name
    #       instead of param_id, which is a pain in the ass
    #       >>> parameter_filter = ParameterFilter.from_element(element,param_name, less_than=10)

    RULES = {
            'equals': 'CreateEqualsRule',
            'not_equals': 'CreateEqualsRule',
            'contains': 'CreateContainsRule',
            'not_contains': 'CreateContainsRule',
            'begins': 'CreateBeginsWithRule',
            'not_begins': 'CreateBeginsWithRule',
            'ends': 'CreateEndsWithRule',
            'not_ends': 'CreateEndsWithRule',
            'greater': 'CreateGreaterRule',
            'not_greater': 'CreateGreaterRule',
            'greater_equal': 'CreateGreaterOrEqualRule',
            'not_greater_equal': 'CreateGreaterOrEqualRule',
            'less': 'CreateLessRule',
            'not_less': 'CreateLessRule',
            'less_equal': 'CreateLessOrEqualRule',
            'not_less_equal': 'CreateLessOrEqualRule',
           }

    CASE_SENSITIVE = True
    FLOAT_PRECISION = 0.0013020833333333

    def __init__(self, parameter_id, **conditions):
        """
        Creates Parameter Filter Rule

        >>> param_rule = ParameterFilter(param_id, equals=2)
        >>> param_rule = ParameterFilter(param_id, not_equals='a', case_sensitive=True)
        >>> param_rule = ParameterFilter(param_id, not_equals=3, reverse=True)

        Args:
            param_id(DB.ElementID): ElemendId of parameter
            **conditions: Filter Rule Conditions and options.

            conditions:
                | ``equals``
                | ``contains``
                | ``begins``
                | ``ends``
                | ``greater``
                | ``greater_equal``
                | ``less``
                | ``less_equal``
                | ``not_equals``
                | ``not_contains``
                | ``not_begins``
                | ``not_ends``
                | ``not_greater``
                | ``not_greater_equal``
                | ``not_less``
                | ``not_less_equal``

            options:
                | ``case_sensitive``: Enforces case sensitive, String only
                | ``reverse``: Reverses result of Collector

        """
        # self.parameter_id = parameter_id
        conditions = conditions
        reverse = conditions.get('reverse', False)
        case_sensitive = conditions.get('case_sensitive', ParameterFilter.CASE_SENSITIVE)
        precision = conditions.get('precision', ParameterFilter.FLOAT_PRECISION)

        for condition in conditions.keys():
            if condition not in ParameterFilter.RULES:
                raise RPW_Exception('Rule not valid: {}'.format(condition))

        rules = []
        for condition_name, condition_value in conditions.iteritems():

            # Returns on of the CreateRule factory method names above
            rule_factory_name = ParameterFilter.RULES.get(condition_name)
            filter_value_rule = getattr(DB.ParameterFilterRuleFactory, rule_factory_name)

            args = [condition_value]

            if isinstance(condition_value, str):
                args.append(case_sensitive)

            if isinstance(condition_value, float):
                args.append(precision)

            # TODO: coerce from BuildInParameter or BIP name into paremter_id
            filter_rule = filter_value_rule(parameter_id, *args)
            if 'not_' in condition_name:
                filter_rule = DB.FilterInverseRule(filter_rule)
            ##################################################################
            # FILTER DEBUG INFO - TODO: MOVE TO FUNCTION
            ##################################################################
            # logger.critical('Conditions: {}'.format(conditions))
            # logger.critical('Case sensitive: {}'.format(case_sensitive))
            # logger.critical('Reverse: {}'.format(self.reverse))
            # logger.critical('ARGS: {}'.format(args))
            # logger.critical(filter_rule)
            # logger.critical(str(dir(filter_rule)))
            ##################################################################
            rules.append(filter_rule)
        if not rules:
            raise RPW_Exception('malformed filter rule: {}'.format(conditions))

        _revit_object = DB.ElementParameterFilter(List[DB.FilterRule](rules), reverse)
        super(ParameterFilter, self).__init__(_revit_object)
        self.conditions = conditions

    def __repr__(self):
        return super(ParameterFilter, self).__repr__(self.conditions)