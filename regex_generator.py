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
    Or, 
    Amount, # Work on character level (need to wrap input into Group in order to become string-level)
    Multi,
    Optional,
    Group,
    # TODO: [ ] Advanced:
    IfAhead,
    IfNotAhead,
    IfBehind,
    IfNotBehind,
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
    @staticmethod
    def get_random_chars(length: int, set_complexity: int) -> typing.List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = [ANY]
        candidates.extend(CharGenerator.special_chars_without_any)
        candidates.extend(CharGenerator.printable_escapes)
        candidates.append(CharGenerator._get_random_range())
        candidates.append(CharGenerator._get_random_set(set_complexity))
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

    @staticmethod
    def _get_random_set(set_complexity: int) -> typing.Union[Set, NotSet]:
        """
        Generate a random Set/NotSet pattern. 
        NOTE that Any (.) is not a special character in set. Hence, it is excluded.
        """
        chars = CharGenerator._get_random_non_repeating_chars(set_complexity)
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

class DynamicCharGenerator:
    """
    Generate repeating chars
    """
    @staticmethod
    def get_random_chars(length: int, set_complexity: int, amount_complexity: int) -> typing.List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = [ANY]
        candidates.extend(CharGenerator.special_chars_without_any)
        candidates.extend(CharGenerator.printable_escapes)
        candidates.append(CharGenerator._get_random_range())
        candidates.append(CharGenerator._get_random_set(set_complexity))
        candidates.append(DynamicCharGenerator._get_random_amount_chars(amount_complexity, set_complexity))
        candidates.append(DynamicCharGenerator._get_random_multi_chars(set_complexity))
        candidates.append(DynamicCharGenerator._get_random_optional_chars(set_complexity))
        return random.choices(candidates, k=length)

    @staticmethod
    def _get_random_amount_chars(amount_complexity: int, set_complexity: int) -> RegexPattern:
        char = CharGenerator.get_random_chars(1, set_complexity)[0]
        if random.uniform(0, 1) < 0.5:
            or_more = True
        else:
            or_more = False
        lower_bound = random.randint(0, amount_complexity)
        if random.uniform(0, 1) < 0.5:
            # no upper bound
            return Amount(char, lower_bound, j = None, or_more = or_more)
        else:
            # with upper bound
            upper_bound = lower_bound + random.randint(0, amount_complexity)
            return Amount(char, lower_bound, j = upper_bound, or_more = or_more)

    @staticmethod    
    def _get_random_multi_chars(set_complexity: int) -> RegexPattern:
        char = CharGenerator.get_random_chars(1, set_complexity)[0]
        if random.uniform(0, 1) < 0.5:
            return Multi(char, match_zero=True)
        else:
            return Multi(char, match_zero=False)
    
    @staticmethod
    def _get_random_optional_chars(set_complexity: int) -> RegexPattern:
        char = CharGenerator.get_random_chars(1, set_complexity)[0]
        return Optional(char)
    


def get_random_plain_pattern(length: int, set_complexity: int, amount_complexity: int) -> RegexPattern:
    """
    A string mixing normal chars with special chars
    """
    return join(*DynamicCharGenerator.get_random_chars(length, set_complexity, amount_complexity))
        
def regex_pattern_generator(repeat_complexity = 10) -> typing.Iterator[RegexPattern]:
    """
    Generate String-level Regex Patterns 
    """
    complexity = 0
    while True:
        for _ in range(repeat_complexity):
            out_str = get_random_plain_pattern(complexity, complexity, complexity)
            yield out_str
        complexity += complexity

if __name__ == '__main__':
    for _ in range(1000):
        regex_pattern = get_random_plain_pattern(10, 8, 3)
        compiled = regex_pattern.compile()
        for _ in range(100):
            print(compiled, ':')
            gen_str = rstr.xeger(regex_pattern.regex)
            print(gen_str)
            assert bool(compiled.fullmatch(gen_str)), f'{gen_str} does not match regex: {compiled}'