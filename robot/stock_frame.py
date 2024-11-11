import numpy as np
import pandas as pd

from datetime import time
from datetime import datetime
from datetime import timezone

from typing import List
from typing import Dict
from typing import Union

from pandas.core.groupby import DataFrameGroupBy
from pandas.core.window import RollingGroupby

class Stockframe():

    def __init__(self, data: List[dict]) -> None:

        self._data = data
        self._frame = pd.DataFrame = self.create_frame()
        self._symbol_groups: DataFrameGroupBy = None
        self._symbol_rolling_groups: RollingGroupby = None

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame
    
    @property
    def symbol_groups(self) -> DataFrameGroupBy:

        self._symbol_groups = self._frame.groupby(
            by='symbol',
            as_index = False,
            sort = True
        )

        return self.symbol_groups

    def symbol_rolling_groups(self, size:int) -> RollingGroupby:
        
        if not self._symbol_groups:
            self.symbol_groups

        self._symbol_rolling_groups = self._symbol_groups.rolling(size)

        return self._symbol_rolling_groups
    
    def create_frame(self) -> pd.DataFrame:

        #Make a data frame
        price_df = pd.DataFrame(data=self._data)
        price_df = self._parse_datatime_column(price_df = price_df)