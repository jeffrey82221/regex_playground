"""
!pip install openai
!pip install langchain
!pip install jskiner
"""
from langchain import PromptTemplate
from langchain.llms import OpenAI
from langchain import LLMChain
from typing import List, Optional, Tuple
import re
class RegexInferencer:
  def __init__(self):
    self._openai_llm = OpenAI(
        openai_api_key='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',
        temperature=0.8
    )
    self._setup_lang_chains()
    self._fail_tolerance = 0.1
    self._max_iteration = 3

  def _setup_lang_chains(self):
    self._regex_alter_chain = LLMChain(
        prompt=self.alter_regex_prompt,
        llm=self._openai_llm
      )
    self._regex_revise_chain = LLMChain(
        prompt=self.revise_regex_prompt,
        llm=self._openai_llm
      )
    self._new_inference_chain = LLMChain(
        prompt=self.new_inference_prompt,
        llm=self._openai_llm
      )
    self._regex_simplify_chain = LLMChain(
        prompt=self.simplify_regex_prompt,
        llm=self._openai_llm
    )

  def run(self, patterns: List[str], regex: Optional[str]=None) -> str:
    if regex is None:
      regex = self._run(patterns)
    regex = self._run_simplify_regex(regex, patterns)
    failed_patterns = self._get_failed_patterns(patterns, regex)
    while failed_patterns:
      failed_regex = self._run(failed_patterns)
      regex = f'{regex}|{failed_regex}'
      regex = self._run_simplify_regex(regex, patterns)
      failed_patterns = self._get_failed_patterns(patterns, regex)
    return regex

  def _run(self, patterns: List[str], regex: Optional[str]=None) -> str:
    if regex:
      regex_result = self._run_alter_regex(regex, patterns)
    else:
      regex_result = self._run_new_inference(patterns)
    regex_result = self._revise_regex(patterns, regex_result)
    return regex_result

  def _run_alter_regex(self, regex: str, patterns: List[str]) -> str:
    for _ in range(self._max_iteration):
      result = self._regex_alter_chain.run(
        regex=regex,
        strings='\n'.join(patterns)).strip()
      try:
        re.compile(result)
        break
      except:
        pass
    return result
  
  def _run_simplify_regex(self, regex: str, patterns: List[str]) -> str:
    for _ in range(self._max_iteration):
      result = self._regex_simplify_chain.run(
        regex=regex,
        strings='\n'.join(patterns)).strip()
      try:
        re.compile(result)
        break
      except:
        pass
    return result
  
  def _run_new_inference(self, patterns: List[str]) -> str:
    for _ in range(self._max_iteration):
      result = self._new_inference_chain.run('\n'.join(patterns)).strip()
      try:
        re.compile(result)
        break
      except:
        pass
    return result

  def _run_revise_regex(self, regex: str, patterns: List[str]) -> str:
    for _ in range(self._max_iteration):
      result = self._regex_revise_chain.run(
          regex=regex,
          strings='\n'.join(patterns)).strip()
      try:
        re.compile(result)
        break
      except:
        pass
    return result

  def _revise_regex(self, patterns: List[str], regex: str) -> str:
    failed_patterns = self._get_failed_patterns(patterns, regex)
    failed_count = len(failed_patterns)
    iter_count = 0
    while len(failed_patterns)/len(patterns) >= self._fail_tolerance:
      regex = self._run_revise_regex(regex, patterns)
      failed_patterns = self._get_failed_patterns(patterns, regex)
      iter_count += 1
      if iter_count > self._max_iteration:
        break
    return regex

  def _get_failed_patterns(self, patterns: List[str], result_regex: str) -> List[str]:
    try:
      re_com = re.compile(result_regex)
    except BaseException as e:
      print('syntax error in result_regex:', result_regex)
      raise e
    result = list(filter(lambda x: re_com.fullmatch(x) is None, patterns))
    return result

  @property
  def new_inference_prompt(self) -> PromptTemplate:
    template = """Question: Show me the best and shortest regex that can fully match the strings that I provide to you.
Note that:
*. The regex should be made more generalized (e.g., use \d to represent digit rather than using [0-9]) and shorter than the original regex.
*. Match sure the resulting regex does not have syntax error.
*. The character count of the resulting regex should not be larger than 30.
*. Use \d to replace [0-9].
*. Try to focus more on the global pattern rather than the local patterns.
Now, the patterns should be fully matched is provided line-by-line as follows:
{strings}

Note: Provide the resulting regex without wrapping it in quote
The resulting regex is: """
    prompt = PromptTemplate(
        template=template,
        input_variables=['strings']
    )
    return prompt

  @property
  def alter_regex_prompt(self) -> PromptTemplate:
    template = """Question: Alter the regex "{regex}" such that the following requirements is matched:
*. The pattern fully match the regex still fully match the regex.
*. The strings that I provide to you also fully match.
*. The character count of the resulting regex should not be larger than 30.
*. The regex should be made more generalized (e.g., use \d to represent digit rather than using [0-9]) and shorter than the original regex.
Each string of the strings is provided line-by-line as follows:
{strings}

Note: Provide the resulting regex without wrapping it in quote
The resulting altered regex is: """
    prompt = PromptTemplate(
        template=template,
        input_variables=['regex', 'strings']
    )
    return prompt

  @property
  def simplify_regex_prompt(self) -> PromptTemplate:
    template = """
Please revise the regex "{regex}"
such that 
*. It becomes as short as possible.
*. It still fully match all the strings full matched the original regex
*. It still fully match each of the following strings:

{strings}

Note: Provide the resulting regex without wrapping it in quote
The resulting revise regex is:
"""
    prompt = PromptTemplate(
        template=template,
        input_variables=['regex', 'strings']
    )
    return prompt

  @property
  def revise_regex_prompt(self) -> PromptTemplate:
    template = """Question: Revise the regex "{regex}" such that the following requirements is matched:
*. The patterns fully match the regex still fully match the revised regex.
*. The regex should be made more generalized (e.g., use \d to represent digit rather than using [0-9]) and shorter than the original regex.
*. Match sure the resulting regex does not have syntax error.
*. Use \d to replace [0-9].
*. Try to focus more on the global pattern rather than the local patterns.
*. The character count of the resulting regex should not be larger than 30.
*. The regex should be revised such that the provided mis-matched strings should be fully matched.

Each string of the mis-matched strings is provided line-by-line as follows:
{strings}

Note: Provide the resulting regex without wrapping it in quote
The resulting altered regex is: """
    prompt = PromptTemplate(
        template=template,
        input_variables=['regex', 'strings']
    )
    return prompt

  @property
  def explain_regex_prompt(self) -> PromptTemplate:
    template = """Question: Explain the regex "{regex}" such that the role of each character in the regex is elaberated

The explaination is: """
    prompt = PromptTemplate(
        template=template,
        input_variables=['regex']
    )
    return prompt

if __name__ == '__main__':
  patterns = [
    "0.0.1",
    "0.0.10",
    "0.0.12",
    "0.0.13",
    "0.0.2",
    "0.0.3",
    "0.0.3.2",
    "0.0.4",
    "0.0.5",
    "0.0.6",
    "0.0.7",
    "0.0.8",
    "0.0.9",
    "0.1",
    "0.1.0",
    "0.1.1",
    "0.1.10",
    "0.1.11",
    "0.1.12",
    "0.1.13",
    "0.1.14",
    "0.1.15",
    "0.1.16",
    "0.1.17",
    "0.1.18",
    "0.1.2",
    "0.1.2a0",
    "0.1.3",
    "0.1.4",
    "0.1.5",
    "0.1.6",
    "0.1.7",
    "0.1.8",
    "0.1.9",
    "0.10",
    "0.11",
    "0.12",
    "0.13",
    "0.14",
    "0.15",
    "0.16",
    "0.17",
    "0.18",
    "0.19",
    "0.2.0",
    "0.2.6",
    "0.20",
    "0.21",
    "0.22",
    "0.23",
    "0.24",
    "0.25",
    "0.26",
    "0.27",
    "0.28",
    "0.29",
    "0.3",
    "0.3.0",
    "0.3.1",
    "0.3.11",
    "0.3.12",
    "0.3.13",
    "0.3.14",
    "0.3.15",
    "0.3.2",
    "0.3.33",
    "0.3.34",
    "0.3.36",
    "0.3.5",
    "0.3.6",
    "0.3.7",
    "0.3.8",
    "0.3.9",
    "0.30",
    "0.4",
    "0.4.6",
    "0.4.7",
    "0.4.8",
    "0.5",
    "0.6",
    "0.7",
    "0.8",
    "1.0",
    "1.0.0",
    "1.0.1",
    "1.0.15",
    "1.0.16",
    "1.0.17",
    "1.0.18",
    "1.0.2",
    "1.0.20",
    "1.0.20200721",
    "1.0.20200723",
    "1.0.20200812",
    "1.0.20200812.1",
    "1.0.20200812.2",
    "1.0.20200812.3",
    "1.0.20200812.4",
    "1.0.20200812.5",
    "1.0.20200812.6",
    "1.0.20200817",
    "1.0.20200820.10",
    "1.0.20200820.8",
    "1.0.20200820.9",
    "1.0.20200820.post2",
    "1.0.20200820.post4",
    "1.0.20200820.post5",
    "1.0.20200820.post6",
    "1.0.20200820.post7",
    "1.0.20200821",
    "1.0.20200821.2",
    "1.0.20200821.3",
    "1.0.20200821.4",
    "1.0.20200824",
    "1.0.20200825",
    "1.0.20200825.10",
    "1.0.20200825.2",
    "1.0.20200825.3",
    "1.0.20200825.4",
    "1.0.20200825.5",
    "1.0.20200825.6",
    "1.0.20200825.7",
    "1.0.20200825.8",
    "1.0.20200825.9",
    "1.0.20200827",
    "1.0.20200827.2",
    "1.0.20200827.3",
    "1.0.20200827.4",
    "1.0.20200827.5",
    "1.0.20200827.6",
    "1.0.20200827.7",
    "1.0.20200827.8",
    "1.0.20200828",
    "1.0.20200828.2",
    "1.0.20200828.3",
    "1.0.20200828.4",
    "1.0.20200829",
    "1.0.20200829.1",
    "1.0.20200829.2",
    "1.0.20200829.3",
    "1.0.20200831",
    "1.0.20200831.2",
    "1.0.3",
    "1.0.4",
    "1.0.5",
    "1.0.6",
    "1.0.7",
    "1.0.8",
    "1.0.9",
    "1.1",
    "1.1.0",
    "1.1.1",
    "1.1.10",
    "1.1.11",
    "1.1.12",
    "1.1.13",
    "1.1.14",
    "1.1.15",
    "1.1.16",
    "1.1.17",
    "1.1.18",
    "1.1.19",
    "1.1.2",
    "1.1.20",
    "1.1.21",
    "1.1.22",
    "1.1.23",
    "1.1.24",
    "1.1.25",
    "1.1.26",
    "1.1.27",
    "1.1.28",
    "1.1.29",
    "1.1.3",
    "1.1.30",
    "1.1.31",
    "1.1.32",
    "1.1.33",
    "1.1.34",
    "1.1.35",
    "1.1.36",
    "1.1.37",
    "1.1.38",
    "1.1.39",
    "1.1.4",
    "1.1.40",
    "1.1.41",
    "1.1.42",
    "1.1.43",
    "1.1.44",
    "1.1.45",
    "1.1.46",
    "1.1.47",
    "1.1.48",
    "1.1.49",
    "1.1.5",
    "1.1.50",
    "1.1.55",
    "1.1.56",
    "1.1.57",
    "1.1.6",
    "1.1.7",
    "1.1.8",
    "1.1.9",
    "1.11",
    "1.12",
    "1.13",
    "1.14",
    "1.15",
    "1.16",
    "1.2.0",
    "1.2.1",
    "1.2.2",
    "1.2.3",
    "1.2.4",
    "1.2.5",
    "1.2.6",
    "1.3.0",
    "1.3.1",
    "1.3.2",
    "1.3.3",
    "1.3.4",
    "1.3.5",
    "1.4.0",
    "2.1.4",
    "2016.4.0",
    "2016.6.0",
    "2017.1.0",
  ]
  ref = RegexInferencer()
  print('pattern count:', len(patterns))
  inference_result = ref.run(patterns)
  print(inference_result)
