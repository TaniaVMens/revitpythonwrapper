"""
Revit Python Wrapper
github.com/gtalarico/revitpythonwrapper
revitpythonwrapper.readthedocs.io

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

Copyright 2017 Gui Talarico

"""

__title__ = 'revitpythonwrapper'
__version__ = '1.0.0'
__maintainer__ = 'Gui Talarico'
__license__ = 'MIT'
__contact__ = 'github.com/gtalarico/revitpythonwrapper'

if __name__ == 'make.doc':
    pass
print __name__

from revit import revit, DB, UI
from rpw.db.collector import *

# from rpw.base import BaseObjectWrapper
# from rpw.element import Element, Instance, Symbol, Family, Category
# from rpw.element import WallInstance, WallSymbol, WallFamily, WallCategory
# from rpw.element import Room, Area, AreaScheme
# from rpw.geometry import Point, PointCollection
# from rpw.parameter import ParameterSet, Parameter
# from rpw.selection import Selection
# from rpw.collector import Collector, ParameterFilter
# from rpw.transaction import Transaction, TransactionGroup
# from rpw.utils.logger import logger
# from rpw.enumeration import BipEnum, BicEnum
# from rpw.utils.coerce import to_element_ids, to_elements

# try:
    # import forms
# except ImportError as errmsg:
    # logger.critical('Could Not load Forms dependencies')
    # logger.warning(errmsg)

# from rpw.utils.sphinx_compat import *
