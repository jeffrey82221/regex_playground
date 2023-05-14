"""
Random FullMatch Regex Generator

NOTE:
regex for fullmatching is simpler than that for search or match

TODO:
- [ ] add selection weight to different kind of special character 
- [ ] use cuckoo filter to ignore repeat regex
- [ ] speed up the generation using multi-processing
"""
import typing
import random
import string
import rstr
import copy
from regexfactory.pattern import escape, join
# TODO: [X] consider random special characters 
from regexfactory.chars import (
    ANY,
    WHITESPACE,
    NOTWHITESPACE,
    WORD,
    NOTWORD,
    DIGIT,
    NOTDIGIT,
    # Currently, we don't consider the start/end anchor because we only do fullmatch.
    # ANCHOR_START, ANCHOR_END
)
from regexfactory.patterns import (
    # TODO: [X] Operators for matching single char: 
    Range, 
    Set,
    NotSet,
    # TODO: [ ] Operators for long string
    Group,
    Or, 
    Amount, # Work on character level (need to wrap input into Group in order to become string-level)
    Multi,
    Optional
    # Commet -> no effect
)
from regexfactory.pattern import RegexPattern

class DynamicWrapper:
    """
    Warp pattern by Amount, Multi, Optional
    """
    @staticmethod
    def wrap_into_amount(pattern: RegexPattern, amount_complexity: int) -> Amount:
        if random.uniform(0, 1) < 0.25:
            or_more = True
        else:
            or_more = False
        lower_bound = random.randint(0, amount_complexity)
        if random.uniform(0, 1) < 0.25:
            # no upper bound
            return Amount(pattern, lower_bound, j = None, or_more = or_more)
        else:
            # with upper bound
            upper_bound = lower_bound + random.randint(0, amount_complexity)
            return Amount(pattern, lower_bound, j = upper_bound, or_more = or_more)
    
    @staticmethod
    def wrap_into_multi(pattern: RegexPattern) -> Multi:
        if random.uniform(0, 1) < 0.5:
            return Multi(pattern, match_zero=True)
        else:
            return Multi(pattern, match_zero=False)

class DynamicCharGenerator:
    """
    All Char-level Generators
    """
    special_chars_without_any = [
        WHITESPACE,
        NOTWHITESPACE,
        WORD,
        NOTWORD,
        DIGIT,
        NOTDIGIT
    ]
    printable_escapes = [escape(x) for x in string.printable]

    def __init__(self, set_complexity: int, amount_complexity: int):
        self._set_complexity = set_complexity
        self._amount_complexity = amount_complexity
        self._start_candidates = DynamicCharGenerator.printable_escapes
        self._start_candidates.extend(DynamicCharGenerator.special_chars_without_any)
        self._start_candidates.append(ANY)

    def get_random_chars(self, length: int) -> typing.List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = copy.copy(self._start_candidates)
        candidates.append(DynamicCharGenerator._get_random_range())
        candidates.append(self._get_random_set())
        char = candidates[random.randint(0, len(candidates)-1)]
        candidates.append(DynamicWrapper.wrap_into_amount(char, self._amount_complexity))
        candidates.append(DynamicWrapper.wrap_into_multi(char))
        candidates.append(Optional(char))
        return random.choices(candidates, k=length)
    
    @staticmethod
    def _get_random_range() -> Range:
        """
        Generate a random regex Range pattern
        [s-e], where s and e are some printable chars
        """
        chars = random.choices(string.printable, k= 2)
        if ord(chars[0]) <= ord(chars[1]):
            return Range(escape(chars[0]), escape(chars[1]))
        else:
            return Range(escape(chars[1]), escape(chars[0]))

    def _get_random_set(self) -> typing.Union[Set, NotSet]:
        """
        Generate a random Set/NotSet pattern. 
        NOTE that Any (.) is not a special character in set. Hence, it is excluded.
        """
        assert self._set_complexity >= 1
        count = random.randint(1, self._set_complexity)
        chars = DynamicCharGenerator._get_random_non_repeating_chars(count)
        pattern = join(*chars)
        if random.uniform(0, 1) > 0.5:
            return Set(pattern)
        else:
            return NotSet(pattern)

    @staticmethod
    def _get_random_non_repeating_chars(count: int) -> typing.List[RegexPattern]:
        """
        Generate a list of single char regex pattern
        without repeat select
        """
        candidates = DynamicCharGenerator.special_chars_without_any + DynamicCharGenerator.printable_escapes
        try:
            result = random.sample(candidates, count)
        except ValueError:
            result = DynamicCharGenerator.printable_escapes
        while (
            (WHITESPACE in result) and (NOTWHITESPACE in result)
        ) or (
            (WORD in result) and (NOTWORD in result)
        ) or (
            (DIGIT in result) and (NOTDIGIT in result)
        ):
            result = random.sample(candidates, count)
        result = sorted(result, key = lambda x: x.regex)
        return result


   

class DynamicGroupGenerator:
    """
    Generate Random Groups wrapped by following things:
    
    TODO:
    - [X] Group,
    - [X] Or, 
    - [X] Amount, # Work on character level (need to wrap input into Group in order to become string-level)
    - [X] Multi,
    - [X] Optional
    """
    def __init__(self, set_complexity: int, union_complexity: int, amount_complexity: int, group_complexity: int, depth_complexity: int, breadth_complexity: int):
        assert breadth_complexity >= 1
        assert set_complexity >= 1
        self._set_complexity = set_complexity
        self._union_complexity = union_complexity
        self._amount_complexity = amount_complexity
        self._group_complexity = group_complexity
        self._depth_complexity = depth_complexity
        self._breadth_complexity = breadth_complexity
        self._dynamic_char_generator = DynamicCharGenerator(set_complexity, amount_complexity)

    def get_random_pattern(self, recurse: int=0) -> RegexPattern:
        """
        Generate random pattern
        """
        group_count = random.randint(0, self._breadth_complexity)
        groups = self.get_random_groups(group_count, recurse=recurse)
        pattern = join(*groups)
        return pattern

    def get_random_groups(self, group_count: int, recurse: int=0) -> typing.List[Group]:
        """
        Generate random group pattern that includes Or/Amount/Multi/Optional patterns
        """
        candidates = []
        while len(candidates) < group_count:
            group = self._get_random_group_pattern(recurse=recurse)
            candidates.append(group)
            candidates.append(self._get_random_union_groups(recurse=recurse))
            candidates.append(Group(DynamicWrapper.wrap_into_amount(group, self._amount_complexity)))
            candidates.append(Group(DynamicWrapper.wrap_into_multi(group)))
            candidates.append(Group(Optional(group)))
        return random.choices(candidates, k=group_count)

    
    def _get_random_union_groups(self, recurse: int=0) -> Group:
        """
        Get random Or-wrapped group patterns
        """
        group_count = random.randint(0, self._union_complexity)
        groups = self._get_random_groups(group_count, recurse=recurse)
        return Group(Or(*groups))
    
    def _get_random_groups(self, group_count: int, recurse: int = 0) -> typing.List[Group]:
        groups = []
        for _ in range(group_count):
            group = self._get_random_group_pattern(recurse=recurse)
            groups.append(group)
        return groups

    
    def _get_random_group_pattern(self, recurse: int=0) -> Group:
        """
        A string mixing normal chars with special chars
        """
        if recurse > self._depth_complexity:
            length = random.randint(0, self._group_complexity)
            return Group(join(*self._dynamic_char_generator.get_random_chars(length)))
        else:
            return Group(self.get_random_pattern(recurse=recurse+1))


class RegexGenerator:
    def __init__(self):
        self._pattern_getter = DynamicGroupGenerator(
            set_complexity=4, 
            union_complexity=1, 
            amount_complexity=3, 
            group_complexity=20, 
            depth_complexity=0, 
            breadth_complexity=1
        )

    def generate(self, validate_cnt=10):
        while True:
            regex_pattern = self._pattern_getter.get_random_pattern()
            if all([self.validate(regex_pattern) for _ in range(validate_cnt)]):
                yield regex_pattern
            else:
                print(f'ignore: {regex_pattern.regex}')
            

    def validate(self, regex_pattern):
        gen_str = rstr.xeger(regex_pattern.regex)
        return bool(regex_pattern.compile().fullmatch(gen_str))
    
if __name__ == '__main__':
    gen = RegexGenerator().generate()
    for x in gen:
        print(x.__repr__())