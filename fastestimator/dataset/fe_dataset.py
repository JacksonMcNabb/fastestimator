# Copyright 2019 The FastEstimator Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import math
import random
from typing import Dict, Any, Union, List, Generator

from torch.utils.data import Dataset


class FEDataset(Dataset):
    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, index: int) -> Dict[str, Any]:
        raise NotImplementedError

    def split(self, *fractions: Union[float, int], method: str = "random") -> Union['FEDataset', List['FEDataset']]:
        assert len(fractions) > 0, "split requires at least one fraction argument"
        original_size = len(self)
        split_types = ("random", "from_front", "from_back")
        assert method in split_types, "split type must be one of {}, but recieved: {}".format(split_types, method)
        frac_sum = 0
        int_sum = 0
        n_samples = []
        for frac in fractions:
            if isinstance(frac, float):
                frac_sum += frac
                frac = math.ceil(original_size * frac)
                int_sum += frac
                n_samples.append(frac)
            elif isinstance(frac, int):
                int_sum += frac
                n_samples.append(frac)
            else:
                raise ValueError("split only accepts float or int type splits, but {} was given".format(frac))
        assert frac_sum < 1, "total split fraction should sum to less than 1.0, but got: {}".format(frac_sum)
        assert int_sum < original_size, \
            "total split requirements ({}) should sum to less than dataset size ({})".format(int_sum, original_size)

        splits = []
        indices = []
        if method == 'random':
            # TODO - convert to a linear congruential generator for large datasets?
            # https://stackoverflow.com/questions/9755538/how-do-i-create-a-list-of-random-numbers-without-duplicates
            indices = random.sample(range(original_size), int_sum)
        elif method == 'from_front':
            indices = [i for i in range(int_sum)]
        elif method == 'from_back':
            indices = [i for i in range(original_size - 1, original_size - int_sum - 1, -1)]
        start = 0
        for stop in n_samples:
            splits.append((indices[i] for i in range(start, start + stop)))
            start += stop
        splits = self._do_split(splits)
        if len(fractions) == 1:
            return splits[0]
        return splits

    def _do_split(self, splits: List[Generator[int, None, None]]) -> List['FEDataset']:
        raise NotImplementedError
