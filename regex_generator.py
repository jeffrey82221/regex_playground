"""
Random FullMatch Regex Generator

NOTE:
regex for fullmatching is simpler than that for search or match

TODO:
- [X] use cuckoo filter to ignore repeat regex
- [ ] generate multiple examples with length > 0
- [ ] add selection weight to different kind of special character
- [ ] speed up the generation using multi-processing
"""
import exrex
import tqdm
import re
from regexfactory import RegexPattern
from toolz import curry
from toolz import curried
from toolz.functoolz import pipe
from rbloom import Bloom
from src.random_pattern import GroupGenerator


class RegexGenerator:
    def __init__(self, max_complexity=10, max_length=30):
        self._max_complexity = max_complexity
        self._max_length = max_length
        self._pattern_getter = GroupGenerator(
            **self.initial_complexities
        )
        self._bloom = Bloom(100000000000, 0.01)

    @property
    def initial_complexities(self) -> dict:
        return {
            'set_complexity': 3, 
            'union_complexity': 1, 
            'amount_complexity': 4, 
            'group_complexity': 20, 
            'depth_complexity': 0, 
            'breadth_complexity': 3
        }
    def produce_regex(self):
        while True:
            yield self._pattern_getter.get_random_pattern()

    def generate(self):
        return pipe(
            self.produce_regex(),
            curried.map(lambda rp: {
                'regex': rp.regex,
                'complexity': exrex.count(rp.regex),
                'length': len(rp.regex)
            }),
            curried.filter(lambda x: x['complexity'] >= 2 and x['complexity']<self._max_complexity),
            curried.filter(lambda x: x['length'] >= 0 and x['length']<self._max_length),
            curried.filter(lambda x: self.valid(x['regex'])),
            self.non_repeat,
            curried.map(self.add_example),
            curried.filter(lambda x: len(x['example']) > 0)
        )
    
    def non_repeat(self, iterable):
        for x in iterable:
            if x['regex'] not in self._bloom:
                yield x
                self._bloom.add(x['regex'])

    def valid(self, regex_str: str) -> bool:
        example = exrex.getone(regex_str)
        return bool(re.compile(regex_str).fullmatch(example))

    def add_example(self, result):
        result['example'] = exrex.getone(result['regex'])
        while not bool(re.compile(result['regex']).fullmatch(result['example'])):
            result['example'] = exrex.getone(result['regex'])
        return result

    def add_examples(self, result):
        """
        Enable generating of multiple examples 
        """
        pass

if __name__ == '__main__':
    gen = RegexGenerator(
        
    ).generate()
    for i, x in enumerate(gen):
        print(i, x)
