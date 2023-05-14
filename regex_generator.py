"""
Random Regex Generator

TODO:
- [ ] add selection weight to different kind of special character 
"""
from typing import List, Iterator, Union
import random
import string
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
    Amount,
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
    def get_random_chars(length, set_complexity) -> List[RegexPattern]:
        """
        Generate a List of single char regex pattern
        with repeat select
        """
        candidates = [ANY]
        candidates.extend(CharGenerator.special_chars_without_any)
        candidates.extend(CharGenerator.printable_escapes)
        candidates.append(CharGenerator.get_random_range())
        candidates.append(CharGenerator.get_random_set(set_complexity))
        return random.choices(candidates, k=length)
            
    @staticmethod
    def get_random_range() -> Range:
        """
        Generate a random regex Range pattern
        [s-e], where s and e are some printable chars
        """
        chars = random.choices(string.printable, k= 2)
        if ord(chars[0]) <= ord(chars[1]):
            return Range(chars[0], chars[1])
        else:
            return Range(chars[1], chars[0])

    @staticmethod
    def get_random_set(char_cnt: int) -> Union[Set, NotSet]:
        """
        Generate a random Set/NotSet pattern. 
        NOTE that Any (.) is not a special character in set. Hence, it is excluded.
        """
        chars = CharGenerator._get_random_non_repeating_chars(char_cnt)
        pattern = join(*chars)
        if random.uniform(0, 1) > 0.5:
            return Set(pattern)
        else:
            return NotSet(pattern)

    @staticmethod
    def _get_random_non_repeating_chars(count: int) -> List[RegexPattern]:
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

    
def get_random_plain_pattern(length, set_complexity) -> RegexPattern:
    """
    A string mixing normal chars with special chars
    """
    return join(*CharGenerator.get_random_chars(length, set_complexity))
        
def plain_generator(repeat_complexity = 10) -> Iterator[RegexPattern]:
    complexity = 0
    while True:
        for _ in range(repeat_complexity):
            out_str = get_random_plain_pattern(complexity, complexity)
            yield out_str
        complexity += complexity