import datetime

import pytest

import pandas as pd

pytest.importorskip("pyarrow", minversion="0.13.0")

from .arrays import ArrowTimestampUSArray  # isort:skip


@pytest.mark.xfail(
    reason="DatetimeTZBlock is created while ExtensionBlock should be, see #34986"
)
def test_constructor_extensionblock():
    # GH 34986
    pd.DataFrame(
        {
            "timestamp": ArrowTimestampUSArray.from_scalars(
                [None, datetime.datetime(2010, 9, 8, 7, 6, 5, 4)]
            )
        }
    )
