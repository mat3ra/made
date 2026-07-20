## To avoid the following problem with spglib
# .venv-3.11.2/lib/python3.11/site-packages/spglib/spglib.py:115
# tests/py/unit/test_tools_build_defect.py::test_create_island
# tests/py/unit/test_tools_build_slab.py::test_build_slab
#   /Users/mat3ra/code/GREEN/stack/lib/made/.venv-3.11.2/lib/python3.11/site-packages/spglib/spglib.py:115:
#   DeprecationWarning: dict interface (SpglibDataset['rotations']) is deprecated.
#   Use attribute interface ({self.__class__.__name__}.{key}) instead
#     warnings.warn(
#
# -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
##

import warnings


def pytest_configure(config):
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="spglib.*")


_orig_warn = warnings.warn


def custom_warn(message, category=None, *args, **kwargs):
    # spglib emits DeprecationWarnings without using `stacklevel`,
    # so pytest and warning filters can't suppress them properly.
    # These warnings always appear to come from inside spglib itself.
    # This patch intercepts `warnings.warn` to ignore only those specific messages.

    if isinstance(message, str) and "SpglibDataset" in message and category is DeprecationWarning:
        return  # suppress
    return _orig_warn(message, category, *args, **kwargs)


warnings.warn = custom_warn
