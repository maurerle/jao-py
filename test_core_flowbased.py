import pandas as pd
from jao import JaoPublicationToolPandasClient
import pytest


@pytest.fixture()
def client():
    client = JaoPublicationToolPandasClient()
    yield client


@pytest.fixture()
def mtu():
    mtu = pd.Timestamp('2023-03-23 12:00', tz='europe/amsterdam')
    yield mtu


def test_final_domain(client, mtu):
    df = client.query_final_domain(
        mtu=mtu,
        presolved=True
    )
    assert len(df) == 117