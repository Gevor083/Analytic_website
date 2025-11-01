# This module delegates to the top-level analytics_app/views.py implementation
# to avoid having a package and a module with the same name (which causes import
# ambiguity). It dynamically loads the top-level views.py file and re-exports
# its public attributes.
import importlib.util
import os
import sys

_here = os.path.dirname(__file__)
_top_views_path = os.path.join(_here, '..', 'views.py')
_top_views_path = os.path.normpath(_top_views_path)

spec = importlib.util.spec_from_file_location('analytics_app._views_impl', _top_views_path)
_module = importlib.util.module_from_spec(spec)
# Insert into sys.modules so relative imports inside views.py work
sys.modules['analytics_app._views_impl'] = _module
spec.loader.exec_module(_module)

# Re-export public attributes
for _name in dir(_module):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_module, _name)

# Provide __all__ for clearer exports
__all__ = [n for n in dir(_module) if not n.startswith('_')]
