import datetime
from unittest.mock import AsyncMock, MagicMock

from yadisk.objects import ResourceObject


async def test_refresh_token_neeaded():
    now_date = datetime.datetime.now();

    yadisk = MagicMock()
    yadisk.listdir = AsyncMock(side_effect=[ResourceObject({"file": 'file1',
                                                            "name": "file_name_1",
                                                            "type": "file",
                                                            "modified" : now_date })])


