"""
Random FullMatch Regex Generator

NOTE:
regex for fullmatching is simpler than that for search or match

TODO:
- [X] use cuckoo filter to ignore repeat regex
- [X] generate multiple examples with length > 0
- [ ] add selection weight to different kind of special character
- [ ] speed up the generation using multi-processing
"""
import exrex
import tqdm
import re
from toolz import curried
from toolz.functoolz import pipe
from rbloom import Bloom
from src.random_pattern import GroupGenerator


class RegexGenerator:
    def __init__(self, max_complexity=1000, max_length=50):
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
            curried.filter(
                lambda x: x['complexity'] > 0 and x['complexity'] < self._max_complexity),
            curried.filter(lambda x: x['length'] >=
                           0 and x['length'] < self._max_length),
            curried.filter(lambda x: self.fullmatch_valid(x['regex'])),
            curried.map(self.add_examples),
            curried.filter(lambda x: isinstance(x['examples'], list)),
            curried.filter(lambda x: len(x['examples']) == x['complexity']),
            curried.filter(self.all_full_match),
            self.non_repeat,
        )

    def non_repeat(self, iterable):
        for x in iterable:
            if x['regex'] not in self._bloom:
                yield x
                self._bloom.add(x['regex'])

    def fullmatch_valid(self, regex_str: str) -> bool:
        """
        Assert fullmatching is possible
        """
        example = exrex.getone(regex_str)
        return bool(re.compile(regex_str).fullmatch(example))

    def all_full_match(self, result: dict) -> bool:
        com = re.compile(result['regex'])
        answers = []
        for example in result['examples']:
            try:
                ans = bool(com.fullmatch(example))
            except TypeError as e:
                if e.args[0] == 'expected string or bytes-like object':
                    return False
                else:
                    raise e
            answers.append(ans)
        return all(answers)

    def add_example(self, result: dict) -> dict:
        """
        Add one single example
        """
        result['example'] = exrex.getone(result['regex'])
        while not bool(re.compile(
                result['regex']).fullmatch(result['example'])):
            result['example'] = exrex.getone(result['regex'])
        return result

    def add_examples(self, result):
        """
        Enable generating of multiple examples
        """
        regex = result['regex']
        try:
            examples = []
            for example in exrex.generate(regex):
                examples.append(example)
            result['examples'] = examples
            return result
        except TypeError as e:
            if e.args[0] == 'can only concatenate list (not "str") to list':
                result['examples'] = None
                return result
            elif e.args[0] == 'can only concatenate str (not "list") to str':
                result['examples'] = None
                return result
            else:
                raise e


if __name__ == '__main__':
    gen = RegexGenerator().generate()
    for i, x in enumerate(gen):
        print(i, x['regex'], len(x['examples']))
