#!/usr/bin/env python3
"""Таблица подкоманд argparse-клиента — из исходника, без запуска.

Файл разбирается модулем ast: он не импортируется и не выполняется, поэтому
скрипт можно натравить на любой клиент, даже на тот, чей импорт логинится,
открывает браузер или что-то отправляет.

    python gen_commands.py ~/.claude/tools/tg_client.py           # Markdown-таблица
    python gen_commands.py ~/.claude/tools/tg_client.py --json    # машинный вывод
    python gen_commands.py client.py --strict    # код 4, если обход что-то не разрешил

Таблица печатается в stdout, сводка и предупреждения — в stderr, так что
`> commands.md` захватывает только таблицу. Перегенерировать после каждой
правки парсера: таблица, написанная руками, расходится с кодом.

Что понимает обход: переиспользуемую переменную (`p = sub.add_parser(...)`),
вложенные add_subparsers любой глубины, функции-помощники (добавляют
аргументы или сами создают подкоманду и возвращают её), циклы по литеральным
спискам и словарям, parents=[...], aliases=[...], async def main().
Чего не понял — не пропускает молча, а пишет в предупреждения со строкой.
"""

import argparse
import ast
import json
import sys
import tokenize
from collections import ChainMap
from dataclasses import dataclass, field

EPILOG = """коды выхода:
  0  таблица готова
  1  файл не читается или не разбирается этим Python
  2  неверные аргументы
  3  в файле нет ни одного add_parser (не argparse-CLI с подкомандами)
  4  с --strict: остались предупреждения
"""


class _Marker:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


UNKNOWN = _Marker("UNKNOWN")  # value the static walk cannot know
NORET = _Marker("NORET")      # statement did not return anything

SUPPRESS = "==SUPPRESS=="
ARGPARSE_CONSTS = {
    "SUPPRESS": SUPPRESS,
    "REMAINDER": "...",
    "OPTIONAL": "?",
    "ZERO_OR_MORE": "*",
    "ONE_OR_MORE": "+",
    "BooleanOptionalAction": "BooleanOptionalAction",
}
ARGPARSE_METHODS = {
    "add_parser", "add_subparsers", "add_argument", "add_argument_group",
    "add_mutually_exclusive_group", "set_defaults",
}
COMMAND_METHODS = {"add_parser", "add_subparsers"}
VALUELESS_ACTIONS = {
    "store_true", "store_false", "store_const", "count", "append_const", "help", "version",
}
SEQ_BUILTINS = {"list", "tuple", "sorted", "reversed", "enumerate", "zip"}
MAX_DEPTH = 12
MAX_LOOP_ITEMS = 2000


@dataclass
class Arg:
    flags: list
    positional: bool
    action: object = None
    nargs: object = None
    required: bool = False
    default: object = None
    choices: object = None
    metavar: object = None
    help: object = None
    hidden: bool = False
    line: int = 0


@dataclass(eq=False)
class Parser:
    path: tuple
    help: str = ""
    aliases: list = field(default_factory=list)
    args: list = field(default_factory=list)
    line: int = 0
    loose: bool = False
    has_sub: bool = False
    handler: object = None
    node_key: tuple = ()


@dataclass(eq=False)
class Subparsers:
    parent: object  # Parser, or None when the owner could not be resolved


@dataclass(eq=False)
class Group:
    parser: Parser


@dataclass(eq=False)
class FuncRef:
    node: ast.AST
    closure: object


ARG_OBJECTS = (Parser, Subparsers, Group)
KNOWN_SCALARS = (str, int, float, bool, type(None))


def node_key(node):
    return (node.lineno, node.col_offset)


def dotted_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def as_sequence(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, dict):
        return list(value.keys())
    return None


def is_known(value):
    """True when value is a plain constant or a container of plain constants."""
    if isinstance(value, KNOWN_SCALARS):
        return True
    if isinstance(value, (list, tuple)):
        return all(is_known(v) for v in value)
    if isinstance(value, dict):
        return all(is_known(k) and is_known(v) for k, v in value.items())
    return False


def merge_ret(a, b):
    """Combine the return values of two code paths; an argparse object wins."""
    if b is NORET:
        return a
    if a is NORET:
        return b
    if isinstance(a, ARG_OBJECTS):
        return a
    if isinstance(b, ARG_OBJECTS):
        return b
    return b if a is UNKNOWN or a is None else a


class Walker:
    """Abstract interpreter for the argparse part of one module.

    It walks statements in source order with an environment of names, so a
    variable reused for every subcommand (`p = sub.add_parser(...)`) is
    rebound each time. A branch whose condition can be computed is followed
    one way; an unknown condition sends the walk down both branches.
    Functions are entered only when they touch argparse or receive an
    argparse object, so the rest of the program is never walked.
    """

    def __init__(self, tree):
        self.tree = tree
        self.module_env = {}
        self.ctor_names = {"ArgumentParser"}
        self.argparse_modules = {"argparse"}
        self.funcs_by_name = {}
        self.all_defs = []
        self.argparse_funcs = set()
        self.ctor_funcs = set()
        self.command_funcs = set()
        self.add_parser_nodes = {}
        self.visited = set()
        self.commands = []
        self.by_path = {}
        self.roots = []
        self.warnings = []
        self.stack = []
        self.inlined = set()
        self._index()

    # ---------------------------------------------------------------- index --
    def _index(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "argparse":
                        self.argparse_modules.add(alias.asname or "argparse")
            elif isinstance(node, ast.ImportFrom) and node.module == "argparse":
                for alias in node.names:
                    local = alias.asname or alias.name
                    if alias.name == "ArgumentParser":
                        self.ctor_names.add(local)
                    elif alias.name in ARGPARSE_CONSTS:
                        self.module_env[local] = ARGPARSE_CONSTS[alias.name]
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.funcs_by_name.setdefault(node.name, []).append(node)
                self.all_defs.append(node)
                for sub in ast.walk(node):
                    if not isinstance(sub, ast.Call):
                        continue
                    f = sub.func
                    if self.is_ctor(f):
                        self.ctor_funcs.add(id(node))
                        self.argparse_funcs.add(id(node))
                    elif isinstance(f, ast.Attribute) and f.attr in ARGPARSE_METHODS:
                        self.argparse_funcs.add(id(node))
                        if f.attr in COMMAND_METHODS:
                            self.command_funcs.add(id(node))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "add_parser"):
                self.add_parser_nodes[node_key(node)] = node.lineno
        self.all_defs.sort(key=lambda n: (n.lineno, n.col_offset))

    def is_ctor(self, func):
        if isinstance(func, ast.Name):
            return func.id in self.ctor_names
        return isinstance(func, ast.Attribute) and func.attr == "ArgumentParser"

    # ------------------------------------------------------------------ run --
    def run(self):
        # 1) the module as a script runs it; 2) parser builders nobody calls
        # (console_scripts entry points); 3) command registrars nobody calls.
        self.walk_body(self.tree.body, self.module_env)
        for group in (self.ctor_funcs, self.command_funcs):
            for fdef in self.all_defs:
                if id(fdef) in group and id(fdef) not in self.inlined:
                    self.call_function(fdef, [], {}, self.module_env)
        loose = [c for c in self.commands if c.loose]
        if loose:
            lines = ", ".join(str(c.line) for c in loose[:20])
            more = "" if len(loose) <= 20 else f" и ещё {len(loose) - 20}"
            self.warn(loose[0].line, f"у {len(loose)} подкоманд не опознан родительский "
                      f"парсер, путь может быть неполным (строки {lines}{more})")
        for key, line in sorted(self.add_parser_nodes.items()):
            if key not in self.visited:
                self.warn(line, "вызов add_parser не достигнут обходом — этой подкоманды нет в таблице")
        self.warnings.sort(key=lambda w: w["line"])
        return self

    def warn(self, line, message):
        item = {"line": line, "message": message}
        if item not in self.warnings:
            self.warnings.append(item)

    # ----------------------------------------------------------- statements --
    def walk_body(self, stmts, env):
        ret = NORET
        for st in stmts:
            ret = merge_ret(ret, self.stmt(st, env))
        return ret

    def stmt(self, st, env):
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            env[st.name] = FuncRef(st, env)
            return NORET
        if isinstance(st, ast.ClassDef):
            return NORET  # methods are reached through calls or as standalone entries
        if isinstance(st, ast.Return):
            return self.eval(st.value, env) if st.value is not None else None
        if isinstance(st, ast.Assign):
            value = self.eval(st.value, env)
            for target in st.targets:
                self.bind(target, value, env)
            return NORET
        if isinstance(st, ast.AnnAssign):
            if st.value is not None:
                self.bind(st.target, self.eval(st.value, env), env)
            return NORET
        if isinstance(st, ast.AugAssign):
            self.eval(st.value, env)
            return NORET
        if isinstance(st, ast.Expr):
            self.eval(st.value, env)
            return NORET
        if isinstance(st, ast.If):
            test = self.eval(st.test, env)
            if test is UNKNOWN or not is_known(test):
                return merge_ret(self.walk_body(st.body, env), self.walk_body(st.orelse, env))
            return self.walk_body(st.body if test else st.orelse, env)
        if isinstance(st, ast.While):
            test = self.eval(st.test, env)
            ret = NORET
            if test is UNKNOWN or not is_known(test) or test:
                ret = self.walk_body(st.body, env)
            return merge_ret(ret, self.walk_body(st.orelse, env))
        if isinstance(st, (ast.For, ast.AsyncFor)):
            return self.for_loop(st, env)
        if isinstance(st, (ast.With, ast.AsyncWith)):
            for item in st.items:
                self.eval(item.context_expr, env)
                if item.optional_vars is not None:
                    self.bind(item.optional_vars, UNKNOWN, env)
            return self.walk_body(st.body, env)
        try_types = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
        if isinstance(st, try_types):
            ret = self.walk_body(st.body, env)
            for handler in st.handlers:
                ret = merge_ret(ret, self.walk_body(handler.body, env))
            ret = merge_ret(ret, self.walk_body(st.orelse, env))
            return merge_ret(ret, self.walk_body(st.finalbody, env))
        if hasattr(ast, "Match") and isinstance(st, ast.Match):
            self.eval(st.subject, env)
            ret = NORET
            for case in st.cases:
                ret = merge_ret(ret, self.walk_body(case.body, env))
            return ret
        for child in ast.iter_child_nodes(st):
            if isinstance(child, ast.expr):
                self.eval(child, env)
        return NORET

    def for_loop(self, st, env):
        items = as_sequence(self.eval(st.iter, env))
        ret = NORET
        if items is not None and len(items) <= MAX_LOOP_ITEMS:
            for item in items:
                self.bind(st.target, item, env)
                ret = merge_ret(ret, self.walk_body(st.body, env))
        else:
            self.bind(st.target, UNKNOWN, env)
            ret = self.walk_body(st.body, env)
        return merge_ret(ret, self.walk_body(st.orelse, env))

    def bind(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            elts = target.elts
            starred = any(isinstance(e, ast.Starred) for e in elts)
            if isinstance(value, (list, tuple)) and len(value) == len(elts) and not starred:
                for e, v in zip(elts, value):
                    self.bind(e, v, env)
            else:
                for e in elts:
                    self.bind(e, UNKNOWN, env)
        elif isinstance(target, ast.Starred):
            self.bind(target.value, UNKNOWN, env)
        elif isinstance(target, ast.Attribute):
            name = dotted_name(target)
            if name is not None:
                env[name] = value
        elif isinstance(target, ast.Subscript):
            base = self.eval(target.value, env)
            key = self.eval(target.slice, env)
            if isinstance(base, dict) and key is not UNKNOWN and is_known(key):
                try:
                    base[key] = value
                except TypeError:
                    pass

    # ---------------------------------------------------------- expressions --
    def lookup(self, name, env):
        if name in env:
            return env[name]
        return self.module_env.get(name, UNKNOWN)

    def eval(self, node, env):
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.lookup(node.id, env)
        if isinstance(node, ast.Call):
            return self.call(node, env)
        if isinstance(node, ast.Attribute):
            name = dotted_name(node)
            if name is not None and name in env:
                return env[name]
            if (node.attr in ARGPARSE_CONSTS and isinstance(node.value, ast.Name)
                    and node.value.id in self.argparse_modules):
                return ARGPARSE_CONSTS[node.attr]
            self.eval(node.value, env)
            return UNKNOWN
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                else:
                    x = self.eval(v.value, env)
                    parts.append(str(x) if isinstance(x, (str, int, float)) else "{…}")
            return "".join(parts)
        if isinstance(node, ast.BinOp):
            left, right = self.eval(node.left, env), self.eval(node.right, env)
            if isinstance(node.op, ast.Add):
                for kind in (str, list, tuple):
                    if isinstance(left, kind) and isinstance(right, kind):
                        return left + right
            return UNKNOWN
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            items, complete = [], True
            for e in node.elts:
                if isinstance(e, ast.Starred):
                    v = self.eval(e.value, env)
                    if isinstance(v, (list, tuple)):
                        items.extend(v)
                    else:
                        complete = False
                else:
                    items.append(self.eval(e, env))
            if not complete:
                return UNKNOWN
            return tuple(items) if isinstance(node, ast.Tuple) else items
        if isinstance(node, ast.Dict):
            out = {}
            for k, v in zip(node.keys, node.values):
                val = self.eval(v, env)
                if k is None:
                    if isinstance(val, dict):
                        out.update(val)
                    continue
                key = self.eval(k, env)
                if key is not UNKNOWN and is_known(key):
                    try:
                        out[key] = val
                    except TypeError:
                        pass
            return out
        if isinstance(node, ast.Subscript):
            base = self.eval(node.value, env)
            idx = self.eval(node.slice, env)
            if isinstance(base, (list, tuple, dict)) and idx is not UNKNOWN and is_known(idx):
                try:
                    return base[idx]
                except (KeyError, IndexError, TypeError):
                    return UNKNOWN
            return UNKNOWN
        if isinstance(node, ast.Await):
            return self.eval(node.value, env)
        if isinstance(node, ast.NamedExpr):
            value = self.eval(node.value, env)
            self.bind(node.target, value, env)
            return value
        if isinstance(node, ast.Lambda):
            return UNKNOWN  # a lambda body runs only when called; not followed
        if isinstance(node, ast.IfExp):
            test = self.eval(node.test, env)
            if test is not UNKNOWN and is_known(test):
                return self.eval(node.body if test else node.orelse, env)
            self.eval(node.body, env)
            self.eval(node.orelse, env)
            return UNKNOWN
        if isinstance(node, ast.UnaryOp):
            v = self.eval(node.operand, env)
            if isinstance(node.op, ast.Not) and v is not UNKNOWN and is_known(v):
                return not v
            return UNKNOWN
        if isinstance(node, ast.BoolOp):
            return self.bool_op(node, env)
        if isinstance(node, ast.Compare):
            return self.compare(node, env)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self.comprehension(node, env)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.eval(child, env)
            elif isinstance(child, ast.comprehension):
                self.eval(child.iter, env)
        return UNKNOWN

    def bool_op(self, node, env):
        is_and = isinstance(node.op, ast.And)
        result = UNKNOWN
        for value_node in node.values:
            v = self.eval(value_node, env)
            if v is UNKNOWN or not is_known(v):
                return UNKNOWN
            result = v
            if is_and and not v:
                return v
            if not is_and and v:
                return v
        return result

    def compare(self, node, env):
        left = self.eval(node.left, env)
        rights = [self.eval(c, env) for c in node.comparators]
        if len(rights) != 1 or not is_known(left) or not is_known(rights[0]):
            return UNKNOWN
        right, op = rights[0], node.ops[0]
        try:
            if isinstance(op, ast.Eq):
                return left == right
            if isinstance(op, ast.NotEq):
                return left != right
            if isinstance(op, ast.In):
                return left in right
            if isinstance(op, ast.NotIn):
                return left not in right
            if isinstance(op, ast.Is):
                return left is right
            if isinstance(op, ast.IsNot):
                return left is not right
        except TypeError:
            return UNKNOWN
        return UNKNOWN

    def comprehension(self, node, env):
        gens = node.generators
        items = as_sequence(self.eval(gens[0].iter, env)) if len(gens) == 1 else None
        if items is None or len(items) > MAX_LOOP_ITEMS:
            for gen in gens:
                self.eval(gen.iter, env)
            self.eval(node.elt, ChainMap({}, env))
            return UNKNOWN
        out = []
        for item in items:
            scope = ChainMap({}, env)
            self.bind(gens[0].target, item, scope)
            keep = [self.eval(cond, scope) for cond in gens[0].ifs]
            if all(c is UNKNOWN or not is_known(c) or c for c in keep):
                out.append(self.eval(node.elt, scope))
        return out

    def eval_args(self, node, env):
        args = []
        for a in node.args:
            if isinstance(a, ast.Starred):
                v = self.eval(a.value, env)
                if isinstance(v, (list, tuple)):
                    args.extend(v)
                else:
                    args.append(UNKNOWN)
            else:
                args.append(self.eval(a, env))
        kwargs = {}
        for kw in node.keywords:
            v = self.eval(kw.value, env)
            if kw.arg is None:
                if isinstance(v, dict):
                    kwargs.update({k: x for k, x in v.items() if isinstance(k, str)})
            else:
                kwargs[kw.arg] = v
        return args, kwargs

    # ---------------------------------------------------------------- calls --
    def call(self, node, env):
        func = node.func
        if self.is_ctor(func):
            args, kwargs = self.eval_args(node, env)
            parser = Parser(path=(), help=self.text(kwargs.get("description")), line=node.lineno)
            self.apply_parents(parser, kwargs.get("parents"))
            self.roots.append(parser)
            return parser
        if isinstance(func, ast.Attribute):
            recv = self.eval(func.value, env)
            meth = func.attr
            if isinstance(recv, ARG_OBJECTS) or (recv is UNKNOWN and meth in ARGPARSE_METHODS):
                return self.argparse_call(recv, meth, node, env)
            args, kwargs = self.eval_args(node, env)
            if isinstance(recv, dict) and meth in ("items", "keys", "values") and not args:
                return list(getattr(recv, meth)())
            if isinstance(recv, list) and meth == "append" and len(args) == 1:
                recv.append(args[0])
                return None
            if isinstance(recv, list) and meth == "extend" and len(args) == 1:
                if isinstance(args[0], (list, tuple)):
                    recv.extend(args[0])
                return None
            fdef = self.unique_def(meth)
            if fdef is not None and self.worth_entering(fdef, args, kwargs):
                receiver = func.value.id if isinstance(func.value, ast.Name) else None
                return self.call_function(fdef, args, kwargs, self.module_env,
                                          caller_env=env, receiver=receiver)
            return UNKNOWN
        if isinstance(func, ast.Name):
            target = self.lookup(func.id, env)
            args, kwargs = self.eval_args(node, env)
            if isinstance(target, FuncRef):
                fdef, closure = target.node, target.closure
            elif target is UNKNOWN and func.id in SEQ_BUILTINS:
                return self.seq_builtin(func.id, args)
            elif target is UNKNOWN:
                fdef, closure = self.unique_def(func.id), self.module_env
            else:
                return UNKNOWN
            if fdef is not None and self.worth_entering(fdef, args, kwargs):
                return self.call_function(fdef, args, kwargs, closure)
            return UNKNOWN
        self.eval(func, env)
        self.eval_args(node, env)
        return UNKNOWN

    def unique_def(self, name):
        defs = self.funcs_by_name.get(name, [])
        return defs[0] if len(defs) == 1 else None

    def worth_entering(self, fdef, args, kwargs):
        if id(fdef) in self.argparse_funcs:
            return True
        return any(isinstance(v, ARG_OBJECTS) for v in list(args) + list(kwargs.values()))

    def seq_builtin(self, name, args):
        if not args:
            return UNKNOWN
        if name == "enumerate":
            items = as_sequence(args[0])
            start = args[1] if len(args) > 1 and isinstance(args[1], int) else 0
            return UNKNOWN if items is None else [(i, x) for i, x in enumerate(items, start)]
        seqs = [as_sequence(a) for a in args]
        if any(s is None for s in seqs):
            return UNKNOWN
        if name == "zip":
            return [tuple(t) for t in zip(*seqs)]
        items = seqs[0]
        if name == "sorted":
            try:
                return sorted(items)
            except TypeError:
                return items
        if name == "reversed":
            return list(reversed(items))
        return tuple(items) if name == "tuple" else items

    def call_function(self, fdef, args, kwargs, closure, caller_env=None, receiver=None):
        """Walk a function body with its parameters bound to the call's values.

        `receiver` is the local name a method was called on (`self` in
        `self.register()`): its dotted attributes are copied in and back out,
        so state kept on the instance survives the call.
        """
        if fdef in self.stack or len(self.stack) >= MAX_DEPTH:
            return UNKNOWN
        local, self_param = self.bind_params(fdef, args, kwargs, is_method=receiver is not None)
        if receiver and self_param and caller_env is not None:
            prefix = receiver + "."
            for k, v in list(caller_env.items()):
                if k.startswith(prefix):
                    local[self_param + "." + k[len(prefix):]] = v
        env = ChainMap(local, closure)
        self.stack.append(fdef)
        self.inlined.add(id(fdef))
        try:
            ret = self.walk_body(fdef.body, env)
        finally:
            self.stack.pop()
        if receiver and self_param and caller_env is not None:
            prefix = self_param + "."
            for k, v in local.items():
                if k.startswith(prefix):
                    caller_env[receiver + "." + k[len(prefix):]] = v
        return UNKNOWN if ret is NORET else ret

    def bind_params(self, fdef, args, kwargs, is_method=False):
        a = fdef.args
        names = [p.arg for p in a.posonlyargs + a.args]
        first_default = len(names) - len(a.defaults)
        local, self_param, pos = {}, None, 0
        args = list(args)
        for i, name in enumerate(names):
            if i == 0 and is_method:
                self_param = name
                local[name] = UNKNOWN
            elif pos < len(args):
                local[name] = args[pos]
                pos += 1
            elif name in kwargs:
                local[name] = kwargs[name]
            elif i >= first_default:
                local[name] = self.eval(a.defaults[i - first_default], ChainMap({}, self.module_env))
            else:
                local[name] = UNKNOWN
        if a.vararg is not None:
            local[a.vararg.arg] = tuple(args[pos:])
        for p, default in zip(a.kwonlyargs, a.kw_defaults):
            if p.arg in kwargs:
                local[p.arg] = kwargs[p.arg]
            elif default is not None:
                local[p.arg] = self.eval(default, ChainMap({}, self.module_env))
            else:
                local[p.arg] = UNKNOWN
        if a.kwarg is not None:
            local[a.kwarg.arg] = {k: v for k, v in kwargs.items() if k not in local}
        return local, self_param

    # -------------------------------------------------------------- argparse --
    def argparse_call(self, recv, meth, node, env):
        args, kwargs = self.eval_args(node, env)
        if isinstance(recv, Group):
            owner = recv.parser
        else:
            owner = recv if isinstance(recv, Parser) else None
        if meth == "add_parser":
            return self.add_parser(recv, node, args, kwargs)
        if meth == "add_subparsers":
            return Subparsers(owner)
        if meth == "add_argument":
            if owner is None:
                self.warn(node.lineno, "add_argument у объекта, который обход не опознал, — "
                                       "аргумент ни к одной подкоманде не привязан")
                return UNKNOWN
            owner.args.append(self.make_arg(args, kwargs, node))
            return UNKNOWN
        if meth in ("add_argument_group", "add_mutually_exclusive_group"):
            return Group(owner) if owner is not None else UNKNOWN
        if meth == "set_defaults" and owner is not None:
            for kw in node.keywords:
                if kw.arg == "func":
                    owner.handler = ast.unparse(kw.value)[:80]
            return None
        return UNKNOWN

    def add_parser(self, recv, node, args, kwargs):
        key = node_key(node)
        self.visited.add(key)
        parent = recv.parent if isinstance(recv, Subparsers) else None
        name = args[0] if args else kwargs.get("name", UNKNOWN)
        if not isinstance(name, str):
            self.warn(node.lineno, "имя подкоманды не вычисляется статически — в таблице записано как <?>")
            name = "<?>"
        path = (parent.path if parent is not None else ()) + (name,)
        text = self.text(kwargs.get("help"))
        if not text:
            text = self.text(kwargs.get("description"))
        raw_aliases = kwargs.get("aliases")
        aliases = ([x for x in raw_aliases if isinstance(x, str)]
                   if isinstance(raw_aliases, (list, tuple)) else [])
        parser = Parser(path=path, help=text, aliases=aliases, line=node.lineno,
                        loose=parent is None, node_key=key)
        self.apply_parents(parser, kwargs.get("parents"))
        prev = self.by_path.get(path)
        if prev is not None:
            if prev.node_key != key:
                self.warn(node.lineno, f"подкоманда «{' '.join(path)}» объявлена второй раз "
                                       f"(первая — строка {prev.line}); в таблице оставлена первая")
            return parser  # same command reached twice: keep the first record
        if parent is not None:
            parent.has_sub = True
        self.by_path[path] = parser
        self.commands.append(parser)
        return parser

    @staticmethod
    def text(value):
        if not isinstance(value, str) or value == SUPPRESS:
            return ""
        return " ".join(value.split())

    @staticmethod
    def apply_parents(parser, parents):
        if isinstance(parents, (list, tuple)):
            for par in parents:
                if isinstance(par, Parser):
                    parser.args.extend(par.args)

    def make_arg(self, args, kwargs, node):
        flags = [a for a in args if isinstance(a, str)]
        if len(flags) != len(args) or not flags:
            self.warn(node.lineno, "имя аргумента не вычисляется статически")
        if not flags:
            flags = ["<?>"]

        def opt(name):
            v = kwargs.get(name)
            return None if v is UNKNOWN else v

        action = kwargs.get("action")
        if action is not None and not isinstance(action, str):
            action = "custom"
        nargs = opt("nargs")
        positional = not flags[0].startswith("-")
        required = (nargs not in ("?", "*", "...")) if positional else bool(opt("required"))
        help_ = kwargs.get("help")
        metavar = opt("metavar")
        return Arg(
            flags=flags, positional=positional, action=action, nargs=nargs,
            required=required, default=opt("default"), choices=opt("choices"),
            metavar=metavar if isinstance(metavar, str) else None,
            help=self.text(help_) or None, hidden=help_ == SUPPRESS, line=node.lineno,
        )

    # ---------------------------------------------------------------- views --
    def global_args(self):
        seen, out = set(), []
        for root in self.roots:
            if not root.has_sub:
                continue
            for a in root.args:
                key = tuple(a.flags)
                if key not in seen and not a.hidden:
                    seen.add(key)
                    out.append(a)
        return out

    def stats(self):
        reached = sum(1 for k in self.add_parser_nodes if k in self.visited)
        return {
            "commands": len(self.commands),
            "top_level": sum(1 for c in self.commands if len(c.path) == 1),
            "nested": sum(1 for c in self.commands if len(c.path) > 1),
            "groups": sum(1 for c in self.commands if c.has_sub),
            "loose": sum(1 for c in self.commands if c.loose),
            "add_parser_calls_in_file": len(self.add_parser_nodes),
            "add_parser_calls_reached": reached,
            "global_args": len(self.global_args()),
            "warnings": len(self.warnings),
        }


def render_value(v):
    if isinstance(v, str) and (not v or any(ch.isspace() for ch in v)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def render_arg(a):
    """Compact usage token: `target`, `[x]`, `text…`, `[--limit=30]`, `--to …`."""
    if a.positional:
        name = a.metavar or a.flags[0]
        if isinstance(a.choices, (list, tuple)) and a.choices and is_known(a.choices):
            name += "{" + ",".join(str(c) for c in a.choices) + "}"
        n = a.nargs
        if n == "?":
            return f"[{name}]"
        if n in ("*", "..."):
            return f"[{name}…]"
        if n == "+":
            return f"{name}…"
        if isinstance(n, int) and n > 1:
            return f"{name}×{n}"
        return name
    flags = "/".join(a.flags)
    if a.action == "BooleanOptionalAction":
        longest = max(a.flags, key=len)
        core = f"{flags}/--no-{longest.lstrip('-')}"
    elif a.action in VALUELESS_ACTIONS:
        core = flags
    else:
        many = a.nargs in ("+", "*") or a.action in ("append", "extend")
        if isinstance(a.choices, (list, tuple)) and a.choices and is_known(a.choices):
            value = "{" + ",".join(str(c) for c in a.choices) + "}"
        else:
            value = a.metavar or "…"
        if many and value != "…":
            value += "…"
        default = a.default
        has_default = isinstance(default, (str, int, float)) and not isinstance(default, bool) \
            and default != "" and default != SUPPRESS  # SUPPRESS = "no default" (multi-level option idiom)
        if has_default and value == "…":
            core = f"{flags}={render_value(default)}"
        elif has_default:
            core = f"{flags} {value}={render_value(default)}"
        else:
            core = f"{flags} {value}"
    return core if a.required else f"[{core}]"


def code(text):
    text = " ".join(str(text).split()).replace("`", "'").replace("|", "\\|")
    return f"`{text}`"


def cell(text):
    return " ".join(str(text).split()).replace("|", "\\|")


def render_markdown(walker):
    lines = []
    globals_ = walker.global_args()
    if globals_:
        lines.append("Общие флаги (ставятся до подкоманды): "
                     + " ".join(code(render_arg(a)) for a in globals_))
        lines.append("")
    lines.append("| Команда | Что делает | Аргументы |")
    lines.append("|---|---|---|")
    for c in walker.commands:
        name = code(" ".join(c.path))
        if c.aliases:
            name += " (" + ", ".join(code(x) for x in c.aliases) + ")"
        args = " ".join(code(render_arg(a)) for a in c.args if not a.hidden)
        lines.append(f"| {name} | {cell(c.help)} | {args} |")
    return "\n".join(lines)


def _jsonable(value):
    if value is UNKNOWN:
        return None
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    return repr(value)


def to_json(walker, path):
    def arg_dict(a):
        return {
            "flags": a.flags, "positional": a.positional, "required": a.required,
            "action": a.action, "nargs": a.nargs, "default": a.default,
            "choices": a.choices, "metavar": a.metavar, "help": a.help,
            "hidden": a.hidden, "usage": render_arg(a), "line": a.line,
        }

    return {
        "file": path,
        "commands": [{
            "name": " ".join(c.path), "path": list(c.path), "help": c.help,
            "aliases": c.aliases, "args": [arg_dict(a) for a in c.args], "line": c.line,
            "has_subcommands": c.has_sub, "loose": c.loose, "handler": c.handler,
        } for c in walker.commands],
        "global_args": [arg_dict(a) for a in walker.global_args()],
        "stats": walker.stats(),
        "warnings": walker.warnings,
    }


def extract(source, filename="<string>"):
    """Parse `source` (never executed) and walk its argparse calls."""
    return Walker(ast.parse(source, filename=filename)).run()


def load(path):
    with tokenize.open(path) as fh:  # honours a PEP 263 coding cookie; read only
        return fh.read()


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(
        prog="gen_commands.py",
        description=__doc__.split("\n\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("file", help="путь к клиенту (.py); файл только читается")
    ap.add_argument("--json", action="store_true", help="машинный вывод вместо Markdown")
    ap.add_argument("--strict", action="store_true",
                    help="код 4, если остались предупреждения (для CI и pre-commit)")
    opts = ap.parse_args(argv)
    try:
        source = load(opts.file)
        walker = extract(source, filename=opts.file)
    except OSError as exc:
        print(f"ОШИБКА: {opts.file} не читается: {exc}. Проверь путь.", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"ОШИБКА: {opts.file} не разбирается этим Python {sys.version.split()[0]}: "
              f"{exc.msg}, строка {exc.lineno}. Проверь, что это Python-файл и что "
              f"интерпретатор не старше синтаксиса файла.", file=sys.stderr)
        return 1
    except ValueError as exc:  # UnicodeDecodeError and bad coding cookies
        print(f"ОШИБКА: {opts.file} не читается как текст: {exc}.", file=sys.stderr)
        return 1
    st = walker.stats()
    if st["add_parser_calls_in_file"] == 0:
        print(f"{opts.file}: ни одного add_parser — это не argparse-CLI с подкомандами "
              f"(одна команда, click, typer или разбор sys.argv). Таблица подкоманд "
              f"к нему неприменима.", file=sys.stderr)
        return 3
    if opts.json:
        print(json.dumps(to_json(walker, opts.file), ensure_ascii=False, indent=2,
                         default=_jsonable))
    else:
        print(render_markdown(walker))
    print(f"{opts.file}: команд {st['commands']} (верхнего уровня {st['top_level']}, "
          f"вложенных {st['nested']}, групп {st['groups']}); add_parser в файле "
          f"{st['add_parser_calls_in_file']}, достигнуто {st['add_parser_calls_reached']}; "
          f"общих флагов {st['global_args']}; предупреждений {st['warnings']}",
          file=sys.stderr)
    for w in walker.warnings:
        print(f"  строка {w['line']}: {w['message']}", file=sys.stderr)
    return 4 if (opts.strict and walker.warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
