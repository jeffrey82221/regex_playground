"""
Random FullMatch Regex Generator

NOTE:
regex for fullmatching is simpler than that for search or match

TODO:
- [ ] add selection weight to different kind of special character 
"""
import typing
import random
import string
import rstr
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
    Optional,
    IfAhead,
    IfNotAhead,
    IfBehind,
    IfNotBehind,
    # TODO: [ ] Advanced:
    IfGroup,
    NamedGroup,
    NamedReference,
    NumberedReference
    # Commet -> no effect
)
from regexfactory.pattern import RegexPattern

class CharGenerator:
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

    def __init__(self, set_complexity: int):
        self._set_complexity = set_complexity

    def get_random_chars(self, length: int) -> typing.List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = [ANY]
        candidates.extend(CharGenerator.special_chars_without_any)
        candidates.extend(CharGenerator.printable_escapes)
        candidates.append(CharGenerator._get_random_range())
        candidates.append(self._get_random_set())
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
        chars = CharGenerator._get_random_non_repeating_chars(count)
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
        candidates = CharGenerator.special_chars_without_any + CharGenerator.printable_escapes
        try:
            result = random.sample(candidates, count)
        except ValueError:
            result = CharGenerator.printable_escapes
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

class DynamicWrapper:
    """
    Warp pattern by Amount, Multi, Optional
    """
    @staticmethod
    def wrap_into_amount(pattern: RegexPattern, amount_complexity: int) -> Amount:
        if random.uniform(0, 1) < 0.5:
            or_more = True
        else:
            or_more = False
        lower_bound = random.randint(0, amount_complexity)
        if random.uniform(0, 1) < 0.5:
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
    Generate repeating chars
    """
    def __init__(self, set_complexity: int, amount_complexity: int): 
        self._set_complexity = set_complexity
        self._amount_complexity = amount_complexity
        self._char_generator = CharGenerator(self._set_complexity)

    def get_random_chars(self, length: int) -> typing.List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = [ANY]
        candidates.extend(CharGenerator.special_chars_without_any)
        candidates.extend(CharGenerator.printable_escapes)
        candidates.append(CharGenerator._get_random_range())
        candidates.append(self._char_generator._get_random_set())
        char = self._char_generator.get_random_chars(1)[0]
        candidates.append(DynamicWrapper.wrap_into_amount(char, self._amount_complexity))
        candidates.append(DynamicWrapper.wrap_into_multi(char))
        candidates.append(Optional(char))
        return random.choices(candidates, k=length)

class DynamicGroupGenerator:
    """
    Generate Random Groups wrapped by following things:
    
    TODO:
    - [X] Group,
    - [X] Or, 
    - [X] Amount, # Work on character level (need to wrap input into Group in order to become string-level)
    - [X] Multi,
    - [X] Optional,
    - [X] IfAhead,
    - [X] IfNotAhead,
    - [X] IfBehind,
    - [X] IfNotBehind,
    """
    def __init__(self, set_complexity: int, union_complexity: int, amount_complexity: int, group_complexity: int):
        self._set_complexity = set_complexity
        self._union_complexity = union_complexity
        self._amount_complexity = amount_complexity
        self._group_complexity = group_complexity
        self._dynamic_char_generator = DynamicCharGenerator(set_complexity, amount_complexity)

    def get_random_group_pattern(self) -> Group:
        """
        Generate random group pattern that includes Or/Amount/Multi/Optional patterns
        """
        candidates = []
        candidates.append(self._get_random_group_pattern())
        candidates.append(self._get_random_union_groups())
        group = self._get_random_group_pattern()
        candidates.append(Group(DynamicWrapper.wrap_into_amount(group, self._amount_complexity)))
        candidates.append(Group(DynamicWrapper.wrap_into_multi(group)))
        candidates.append(Group(Optional(group)))
        #candidates.append(Group(IfAhead(group)))
        #candidates.append(Group(IfNotAhead(group)))
        #candidates.append(Group(IfBehind(group)))
        #candidates.append(Group(IfNotBehind(group)))
        return random.choices(candidates, k=1)[0]

    
    def _get_random_union_groups(self) -> Group:
        """
        Get random Or-wrapped group patterns
        """
        group_count = random.randint(0, self._union_complexity)
        groups = self._get_random_groups(group_count)
        return Group(Or(*groups))
    
    def _get_random_groups(self, group_count: int) -> typing.List[Group]:
        groups = []
        for _ in range(group_count):
            group = self._get_random_group_pattern()
            groups.append(group)
        return groups

    
    def _get_random_group_pattern(self) -> Group:
        """
        A string mixing normal chars with special chars

        TODO:
        - [ ] Make this function becomes the core of recurrsive
        """
        length = random.randint(0, self._group_complexity)
        return Group(join(*self._dynamic_char_generator.get_random_chars(length)))
        

if __name__ == '__main__':
    d = DynamicGroupGenerator(10, 8, 3, 3)
    for _ in range(1000):
        regex_pattern = d.get_random_group_pattern()
        compiled = regex_pattern.compile()
        for _ in range(100):
            print(compiled, ':')
            gen_str = rstr.xeger(regex_pattern.regex)
            print(gen_str)
            assert bool(compiled.fullmatch(gen_str)), f'{gen_str} does not match regex: {compiled}'