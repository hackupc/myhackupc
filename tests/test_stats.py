import json

import pytest

from applications.models.hacker import HackerApplication
from stats.views import get_stats
from tests.factories import HackerApplicationFactory


@pytest.mark.django_db
def test_tshirt_stats_sorted_by_size():
    for size in ["L", "XS", "XXL", "M"]:
        HackerApplicationFactory(tshirt_size=size)

    data = json.loads(get_stats(HackerApplication).content)

    assert [row["tshirt"] for row in data["tshirt"]] == [
        "Unisex - XS", "Unisex - M", "Unisex - L", "Unisex - XXL",
    ]
