#!/usr/bin/env python3

"""
Handle multi-args as specified by
https://github.com/docopt/docopt/issues/134


__doc__ = \"\"\"

Usage:  test1 help
        test1 (-C CONF | --conf CONF)... cmd1
        test1 (-C CONF | --conf CONF)... cmd1
              [-b bonf]
        test1 (-C CONF | --conf CONF)... cmd
        test1 (-D DONF | --donf DONF)... cmd

Options:

    -C=CONF, --conf=CONF  The conf
    -D=DONF, --donf=DONF  The donf
    -b=BONF    The bonf

\"\"\"

doc2 = \"\"\"
Usage:  test1 help
        test1 (-C CONF)... cmd1
        test1 (-C CONF)... cmd1
              [-b bonf]
        test1 (-C CONF)... cmd
        test1 (-D DONF)... cmd

Options:

    -C=CONF  The conf
    -D=DONF  The donf
    -b=BONF  The bonf

\"\"\"

if __name__ == '__main__':
    print(f"From {opts} ")

    print(f"To {clean_multi_args(opts, __doc__, use_dual_options=True)}")

    print(f"From {opts2} ")
    print(f"To {clean_multi_args(opts2, doc2, use_dual_options=False)}")

with
python foo.py -C a -C b -C c -C d -b aaa cmd1

Yields

From {'--conf': ['a', 'b', 'b', 'c', 'c', 'd', 'd', 'b', 'b', 'c', 'c', 'd', 'd', 'b', 'b', 'c', 'c', 'd', 'd'],
 '--donf': [],
 '-b': 'sdf',
 'cmd': False,
 'cmd1': True,
 'help': False}
To {'--conf': ['a', 'b', 'c', 'd'],
 '--donf': [],
 '-b': 'sdf',
 'cmd': False,
 'cmd1': True,
 'help': False}
From {'-C': ['a', 'b', 'c', 'd', 'b', 'c', 'd', 'b', 'c', 'd'],
 '-D': [],
 '-b': 'sdf',
 'cmd': False,
 'cmd1': True,
 'help': False}
To {'-C': ['a', 'b', 'c', 'd'],
 '-D': [],
 '-b': 'sdf',
 'cmd': False,
 'cmd1': True,
 'help': False}
"""

from copy import deepcopy

import docopt
from docopt import \
    parse_pattern, parse_defaults, \
    formal_usage, \
    Option, OneOrMore, \
    Required

import re
from math import ceil
from functools import reduce

from typing import Dict, List


def parse_section(name, source):
    # Cant import this so as defined here
    # https://github.com/docopt/docopt/blob/20b9c4ffec71d17cee9fd963238c8ec240905b65/docopt.py#L464-L467
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


def splice_list(lst, n) -> List[List]:
    """
    Take every nth element from a list
    Repeat with an offset of 1..1-n
    :param lst:
    :param n:
    :return:
    """
    return list(
        lst[i::n]
        for i in range(n)
    )


def chunk_into_n(lst, n):
    """
    Split list into 'n' sized chunks
    # From https://www.30secondsofcode.org/python/s/chunk-into-n
    :param lst:
    :param n:
    :return:
    """
    size = ceil(len(lst) / n)
    return list(
        map(lambda x: lst[x * size:x * size + size],
            list(range(n)))
    )


def parse_usage(doc: str) -> str:
    """
    Parses the usage section from the doc string
    :param doc:
    :return:
    """
    # Can assume number of usages is 1 from
    # https://github.com/docopt/docopt/blob/20b9c4ffec71d17cee9fd963238c8ec240905b65/docopt.py#L555-L560
    usages = parse_section("usage:", doc)
    assert len(usages) == 1
    return usages[0]


def get_pattern(usage: str, doc: str) -> Required:
    """
    Collect the Required pattern docopt
    :param usage:
    :param doc:
    :return:
    """
    return parse_pattern(
        formal_usage(usage),
        parse_defaults(doc)
    )


def get_multi_args(pattern: Required) -> List[str]:
    """
    Get all the mult-args for all the usages
    :param pattern:
    :return:
    """
    multi_args = pattern.flat(OneOrMore)

    if isinstance(multi_args, List):
        # Return an empty list if there are no multi args
        # Since reduce function cannot handle an empty list
        if len(multi_args) == 0:
            return multi_args
        multi_args = reduce(
            lambda a, b: a + b,
            [
                multi_pattern.flat(Option)
                for multi_pattern in multi_args
            ]
        )

    return [
        arg.name
        for arg in multi_args
    ]


def get_num_usages_for_multi_arg(pattern: Required, arg_name: str) -> int:
    """
    How many patterns are returned
    :param pattern:
    :param arg_name:
    :return:
    """
    return len(
        list(
            filter(
                lambda option: option.name == arg_name,
                pattern.flat(Option)
            )
        )
    )


def clean_multi_arg(arg_vals: List, num_usages, use_dual_options) -> List:
    """
    Additional args after the first arg are duplicated by the number of usages
    that this argument is present in
    :param arg_vals:
    :param num_usages:
    :param use_dual_options:
    :return:
    """
    # Not an issue if only one value
    if len(arg_vals) <= 1:
        return arg_vals

    # Do we use short and long args for this option?
    if use_dual_options:
        # Half usages if we use dual options
        num_usages = num_usages / 2

    # Drop repetitions caused by multiple usages
    args_split = chunk_into_n(arg_vals[1:], int(num_usages))

    assert all(
        args_split[0] == list_iter
        for list_iter in args_split[1:]
    )
    args_split = args_split[0]

    if use_dual_options:
        # Drop repetitions caused by using both
        # short and long-hand options
        args_split = splice_list(args_split, 2)

        # Assert we have split correct by
        # Checking all chunks are the same
        assert all(
            args_split[0] == list_iter
            for list_iter in args_split[1:]
        )
        args_split = args_split[0]

    return [arg_vals[0]] + args_split


def clean_multi_args(args: Dict, doc: str, use_dual_options: bool) -> Dict:
    """
    Clean args that can be invoked multiple times
    Set the use_dual_options parameter if your syntax is like [-a=<arg_val> | --arg=<arg_val]...
    :param args:
    :param doc:
    :param use_dual_options:
    :return:
    """
    # Copy over args to reduce affects in global scope
    args = deepcopy(args)

    # Get the usage
    usage = parse_usage(doc)

    # Get the pattern
    pattern = parse_pattern(
        formal_usage(usage),
        parse_defaults(doc)
    )

    # Get all the --keys of multi-args in usage
    multi_arg_names = get_multi_args(pattern)

    # Clean each multi-arg
    fixed_args = {}
    for multi_arg_name in multi_arg_names:
        if multi_arg_name not in args.keys():
            continue
        num_usages = get_num_usages_for_multi_arg(
            pattern,
            multi_arg_name
        )
        fixed_args[multi_arg_name] = clean_multi_arg(
            args.get(multi_arg_name),
            num_usages,
            use_dual_options=use_dual_options
        )
    args.update(
        fixed_args
    )

    return args

