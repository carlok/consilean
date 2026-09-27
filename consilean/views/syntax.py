"""A small statement parser and the curated normal form.

The normal form is the one named in the preregistration: map `IsSquare` in
`ZMod` to an integer congruence, and treat `[ZMOD t.natAbs]` as `[ZMOD t]`.
Bound variables are then renamed in binding order, so the score tracks
notation rather than the letters chosen for binders.
"""

from __future__ import annotations

from dataclasses import dataclass

_SYMBOLS = ("↔", "→", "∃", "∀", "≡", "∧", "∨", "∣", "≠", "≤", "≥", "∈", "∉", "⊆", "⊇", "⁻¹", "<", ">", "/")
_SINGLE = set("()[]{}:,^+-*=.")


class ParseError(Exception):
    """The statement is outside the fragment this parser accepts."""


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    name: str


@dataclass(frozen=True)
class Proj:
    base: object
    field: str


@dataclass(frozen=True)
class App:
    fn: object
    arg: object


@dataclass(frozen=True)
class Bin:
    op: str
    left: object
    right: object


@dataclass(frozen=True)
class Neg:
    arg: object


@dataclass(frozen=True)
class Ascribe:
    val: object
    ty: object


@dataclass(frozen=True)
class ModEq:
    left: object
    right: object
    modulus: object


@dataclass(frozen=True)
class Quant:
    kind: str
    var: str
    ty: object | None
    body: object


@dataclass(frozen=True)
class Postfix:
    arg: object
    op: str


@dataclass(frozen=True)
class Index:
    base: object
    index: object


@dataclass(frozen=True)
class NatLit:
    value: str


@dataclass(frozen=True)
class Binder:
    name: str
    ty: object


@dataclass(frozen=True)
class Statement:
    binders: tuple[Binder, ...]
    body: object


def tokenize(source: str) -> list[str]:
    """Split a Lean signature into tokens. Dots stay inside identifiers."""
    tokens: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        if source[i].isspace():
            i += 1
            continue
        if source.startswith(_SYMBOLS, i):
            for symbol in _SYMBOLS:
                if source.startswith(symbol, i):
                    tokens.append(symbol)
                    i += len(symbol)
                    break
            continue
        if source[i] in _SINGLE:
            tokens.append(source[i])
            i += 1
            continue
        if source[i].isdigit():
            j = i + 1
            while j < n and source[j].isdigit():
                j += 1
            tokens.append(source[i:j])
            i = j
            continue
        j = i + 1
        while j < n and _ident_char(source[j]):
            j += 1
        while j < n and source[j] == ".":
            k = j + 1
            while k < n and _ident_char(source[k]):
                k += 1
            if k == j + 1:
                break
            j = k
        if source[i:j] in {"Type", "Sort"} and j < n and source[j] == "*":
            j += 1
        if j == i:
            raise ParseError(source[i])
        tokens.append(source[i:j])
        i = j
    return tokens


def parse_statement(source: str) -> Statement | None:
    """Parse binders and a result type. Return None when the fragment does not fit."""
    try:
        parser = _Parser(tokenize(source))
        statement = parser.statement()
        if not parser.done():
            return None
        return statement
    except ParseError:
        return None


def normal_form(source: str) -> str | None:
    """Canonical text after the curated rewrites and binder renaming."""
    statement = parse_statement(source)
    if statement is None:
        return None
    return pretty_statement(alpha_statement(rewrite_statement(statement)))


def rewrite_statement(statement: Statement) -> Statement:
    return Statement(
        tuple(Binder(binder.name, _rewrite(binder.ty)) for binder in statement.binders),
        _rewrite(statement.body),
    )


def alpha_statement(statement: Statement) -> Statement:
    """Rename binders to v0, v1, … in the order they are bound."""
    counter = 0

    def fresh() -> str:
        nonlocal counter
        name = f"v{counter}"
        counter += 1
        return name

    def rename(expr: object, env: dict[str, str]) -> object:
        if isinstance(expr, Var):
            return Var(env.get(expr.name, expr.name))
        if isinstance(expr, (Const, NatLit)):
            return expr
        if isinstance(expr, Proj):
            return Proj(rename(expr.base, env), expr.field)
        if isinstance(expr, App):
            return App(rename(expr.fn, env), rename(expr.arg, env))
        if isinstance(expr, Bin):
            return Bin(expr.op, rename(expr.left, env), rename(expr.right, env))
        if isinstance(expr, Postfix):
            return Postfix(rename(expr.arg, env), expr.op)
        if isinstance(expr, Index):
            return Index(rename(expr.base, env), rename(expr.index, env))
        if isinstance(expr, Neg):
            return Neg(rename(expr.arg, env))
        if isinstance(expr, Ascribe):
            return Ascribe(rename(expr.val, env), rename(expr.ty, env))
        if isinstance(expr, ModEq):
            return ModEq(
                rename(expr.left, env),
                rename(expr.right, env),
                rename(expr.modulus, env),
            )
        if isinstance(expr, Quant):
            ty = rename(expr.ty, env) if expr.ty is not None else None
            new = fresh()
            inner = dict(env)
            inner[expr.var] = new
            return Quant(expr.kind, new, ty, rename(expr.body, inner))
        raise TypeError(type(expr))

    env: dict[str, str] = {}
    binders: list[Binder] = []
    for binder in statement.binders:
        ty = rename(binder.ty, env)
        new = fresh()
        env[binder.name] = new
        binders.append(Binder(new, ty))
    return Statement(tuple(binders), rename(statement.body, env))


def as_forall(source: str) -> str | None:
    """The signature as a Lean proposition, or None if it does not parse.

    Binders stay in the source's own names. This is the goal fed to a probe,
    not the normal form.
    """
    statement = parse_statement(source)
    if statement is None:
        return None
    body = pretty(statement.body)
    if not statement.binders:
        return body
    binders = " ".join(f"({binder.name} : {pretty(binder.ty)})" for binder in statement.binders)
    return f"∀ {binders}, {body}"


def pretty_statement(statement: Statement) -> str:
    parts = [f"({binder.name} : {pretty(binder.ty)})" for binder in statement.binders]
    body = pretty(statement.body)
    if parts:
        return " ".join(parts) + " : " + body
    return body


def pretty(expr: object) -> str:
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, Const):
        return expr.name
    if isinstance(expr, NatLit):
        return expr.value
    if isinstance(expr, Proj):
        return f"{pretty(expr.base)}.{expr.field}"
    if isinstance(expr, App):
        return f"{pretty(expr.fn)} {_atom(expr.arg)}"
    if isinstance(expr, Postfix):
        return f"{pretty(expr.arg)}{expr.op}"
    if isinstance(expr, Index):
        return f"{pretty(expr.base)}[{pretty(expr.index)}]"
    if isinstance(expr, Neg):
        return f"-{_atom(expr.arg)}"
    if isinstance(expr, Ascribe):
        return f"({pretty(expr.val)} : {pretty(expr.ty)})"
    if isinstance(expr, Bin):
        return f"{pretty(expr.left)} {expr.op} {pretty(expr.right)}"
    if isinstance(expr, ModEq):
        return f"{pretty(expr.left)} ≡ {pretty(expr.right)} [ZMOD {pretty(expr.modulus)}]"
    if isinstance(expr, Quant):
        head = "∃" if expr.kind == "exists" else "∀"
        if expr.ty is None:
            return f"{head} {expr.var}, {pretty(expr.body)}"
        return f"{head} {expr.var} : {pretty(expr.ty)}, {pretty(expr.body)}"
    raise TypeError(type(expr))


def formula_graph(statement: Statement, *, keep_names: bool) -> tuple[list[str], list[list[tuple[str, int]]]]:
    """Undirected-ready formula graph. Bound variables share a node.

    Name-free mode labels every constant `const`. The keep-names mode keeps
    the identifier on that label. This is the Lean shape of euclean's formula
    graph: argument position is an edge label, and a variable is one node.
    """
    labels: list[str] = []
    adj: list[list[tuple[str, int]]] = []
    var_node: dict[str, int] = {}

    def new(label: str) -> int:
        labels.append(label)
        adj.append([])
        return len(labels) - 1

    def link(src: int, dst: int, label: str) -> None:
        adj[src].append((label, dst))
        adj[dst].append((f"^{label}", src))

    def var(name: str) -> int:
        if name not in var_node:
            var_node[name] = new("var:bound")
        return var_node[name]

    def const_label(name: str) -> str:
        return f"const:{name}" if keep_names else "const"

    def go(expr: object) -> int:
        if isinstance(expr, Var):
            return var(expr.name)
        if isinstance(expr, Const):
            return new(const_label(expr.name))
        if isinstance(expr, NatLit):
            return new(f"nat:{expr.value}")
        if isinstance(expr, Proj):
            node = new(const_label(expr.field))
            link(node, go(expr.base), "arg0")
            return node
        if isinstance(expr, App):
            node = new("app")
            link(node, go(expr.fn), "fn")
            link(node, go(expr.arg), "arg0")
            return node
        if isinstance(expr, Bin):
            node = new(expr.op)
            link(node, go(expr.left), "arg0")
            link(node, go(expr.right), "arg1")
            return node
        if isinstance(expr, Postfix):
            node = new(expr.op)
            link(node, go(expr.arg), "arg0")
            return node
        if isinstance(expr, Index):
            node = new("index")
            link(node, go(expr.base), "arg0")
            link(node, go(expr.index), "arg1")
            return node
        if isinstance(expr, Neg):
            node = new("neg")
            link(node, go(expr.arg), "arg0")
            return node
        if isinstance(expr, Ascribe):
            node = new("ascribe")
            link(node, go(expr.val), "arg0")
            link(node, go(expr.ty), "arg1")
            return node
        if isinstance(expr, ModEq):
            node = new("modEq")
            link(node, go(expr.left), "arg0")
            link(node, go(expr.right), "arg1")
            link(node, go(expr.modulus), "mod")
            return node
        if isinstance(expr, Quant):
            var(expr.var)
            node = new(expr.kind)
            if expr.ty is not None:
                link(node, go(expr.ty), "ty")
            link(node, go(expr.body), "body")
            return node
        raise TypeError(type(expr))

    for binder in statement.binders:
        var(binder.name)
        node = new("binder")
        link(node, var(binder.name), "var")
        link(node, go(binder.ty), "ty")
    go(statement.body)
    return labels, adj


def _ident_char(char: str) -> bool:
    if char in _SINGLE or char.isspace() or char in "".join(_SYMBOLS):
        return False
    return True


def _atom(expr: object) -> str:
    if isinstance(expr, (Var, Const, NatLit, Proj, Neg, Ascribe)):
        return pretty(expr)
    return f"({pretty(expr)})"


def _strip_nat_abs(expr: object) -> object:
    if isinstance(expr, Proj) and expr.field == "natAbs":
        return expr.base
    return expr


def _rewrite(expr: object) -> object:
    expr = _map(_rewrite, expr)
    rewritten = _is_square_zmod(expr)
    if isinstance(rewritten, ModEq):
        return ModEq(rewritten.left, rewritten.right, _strip_nat_abs(rewritten.modulus))
    return rewritten


def _is_square_zmod(expr: object) -> object:
    if not isinstance(expr, App) or not isinstance(expr.fn, Const) or expr.fn.name != "IsSquare":
        return expr
    arg = expr.arg
    if not isinstance(arg, Ascribe) or not isinstance(arg.ty, App):
        return expr
    if not isinstance(arg.ty.fn, Const) or arg.ty.fn.name != "ZMod":
        return expr
    modulus = _strip_nat_abs(arg.ty.arg)
    return Quant(
        "exists",
        "r",
        Const("ℤ"),
        ModEq(Bin("^", Var("r"), NatLit("2")), arg.val, modulus),
    )


def _map(fn, expr: object) -> object:
    if isinstance(expr, (Var, Const, NatLit)):
        return expr
    if isinstance(expr, Proj):
        return Proj(fn(expr.base), expr.field)
    if isinstance(expr, App):
        return App(fn(expr.fn), fn(expr.arg))
    if isinstance(expr, Bin):
        return Bin(expr.op, fn(expr.left), fn(expr.right))
    if isinstance(expr, Postfix):
        return Postfix(fn(expr.arg), expr.op)
    if isinstance(expr, Index):
        return Index(fn(expr.base), fn(expr.index))
    if isinstance(expr, Neg):
        return Neg(fn(expr.arg))
    if isinstance(expr, Ascribe):
        return Ascribe(fn(expr.val), fn(expr.ty))
    if isinstance(expr, ModEq):
        return ModEq(fn(expr.left), fn(expr.right), fn(expr.modulus))
    if isinstance(expr, Quant):
        ty = fn(expr.ty) if expr.ty is not None else None
        return Quant(expr.kind, expr.var, ty, fn(expr.body))
    raise TypeError(type(expr))


def _is_name(token: str) -> bool:
    if token in _SYMBOLS or token in _SINGLE or token.isdigit():
        return False
    return token[:1].isalnum() or token[:1] == "_"


def _resolve(name: str, bound: set[str]) -> object:
    parts = name.split(".")
    if parts[0] in bound:
        node: object = Var(parts[0])
        for field in parts[1:]:
            node = Proj(node, field)
        return node
    return Const(name)


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.i = 0
        self.bound: set[str] = set()

    def done(self) -> bool:
        return self.i >= len(self.tokens)

    def peek(self) -> str | None:
        if self.done():
            return None
        return self.tokens[self.i]

    def pop(self) -> str:
        token = self.peek()
        if token is None:
            raise ParseError("end")
        self.i += 1
        return token

    def expect(self, token: str) -> None:
        if self.pop() != token:
            raise ParseError(token)

    def statement(self) -> Statement:
        binders: list[Binder] = []
        while self.peek() in {"(", "{", "["}:
            binders.extend(self._binder_group())
        if self.peek() == ":":
            self.pop()
        elif binders:
            raise ParseError("colon")
        return Statement(tuple(binders), self.expr())

    def _binder_group(self) -> list[Binder]:
        opener = self.pop()
        closer = { "(": ")", "{": "}", "[": "]" }[opener]
        if opener == "[" and self.peek() != "]" and not self._binder_has_colon():
            ty = self.expr()
            self.expect(closer)
            return [Binder("_inst", ty)]
        names: list[str] = []
        while _is_name(self.peek() or ""):
            names.append(self.pop())
        if not names:
            raise ParseError("binder")
        self.expect(":")
        ty = self.expr()
        self.expect(closer)
        for name in names:
            self.bound.add(name)
        return [Binder(name, ty) for name in names]

    def _binder_has_colon(self) -> bool:
        """Look ahead for `:` before the matching `]`."""
        depth = 1
        index = self.i
        while index < len(self.tokens) and depth:
            token = self.tokens[index]
            if token == "[":
                depth += 1
            elif token == "]":
                depth -= 1
            elif token == ":" and depth == 1:
                return True
            index += 1
        return False

    def expr(self) -> object:
        return self._iff()

    def _iff(self) -> object:
        left = self._arrow()
        if self.peek() == "↔":
            self.pop()
            return Bin("↔", left, self._iff())
        return left

    def _arrow(self) -> object:
        left = self._and()
        if self.peek() == "→":
            self.pop()
            return Bin("→", left, self._arrow())
        return left

    def _and(self) -> object:
        left = self._eq()
        while self.peek() in {"∧", "∨"}:
            op = self.pop()
            left = Bin(op, left, self._eq())
        return left

    def _eq(self) -> object:
        left = self._add()
        if self.peek() not in {"=", "≡", "≤", "≥", "<", ">", "≠", "∈", "∉", "⊆", "⊇"}:
            return left
        op = self.pop()
        right = self._add()
        if op == "≡" and self.peek() == "[":
            self.pop()
            if self.pop() != "ZMOD":
                raise ParseError("ZMOD")
            modulus = self._add()
            self.expect("]")
            return ModEq(left, right, modulus)
        return Bin(op, left, right)

    def _add(self) -> object:
        left = self._mul()
        while self.peek() in {"+", "-"}:
            op = self.pop()
            left = Bin(op, left, self._mul())
        return left

    def _mul(self) -> object:
        left = self._pow()
        while self.peek() in {"*", "/"}:
            op = self.pop()
            left = Bin(op, left, self._pow())
        return left

    def _pow(self) -> object:
        left = self._unary()
        if self.peek() != "^":
            return left
        self.pop()
        return Bin("^", left, self._unary())

    def _unary(self) -> object:
        if self.peek() == "-":
            self.pop()
            return Neg(self._unary())
        return self._app()

    def _app(self) -> object:
        node = self._postfix(self._atom())
        while self._starts_atom():
            node = App(node, self._postfix(self._atom()))
        return node

    def _next_is(self, token: str) -> bool:
        return self.i + 1 < len(self.tokens) and self.tokens[self.i + 1] == token

    def _postfix(self, node: object) -> object:
        while self.peek() == "⁻¹" or (self.peek() == "[" and not self._next_is("ZMOD")):
            if self.peek() == "⁻¹":
                self.pop()
                node = Postfix(node, "⁻¹")
                continue
            self.pop()
            index = self.expr()
            self.expect("]")
            node = Index(node, index)
        return node

    def _starts_atom(self) -> bool:
        token = self.peek()
        if token is None:
            return False
        return token in {"(", "∃", "∀"} or token.isdigit() or _is_name(token)

    def _atom(self) -> object:
        token = self.peek()
        if token is None:
            raise ParseError("atom")
        if token == "(":
            self.pop()
            expr = self.expr()
            if self.peek() == ":":
                self.pop()
                expr = Ascribe(expr, self.expr())
            self.expect(")")
            return expr
        if token == "∃":
            return self._quant("exists")
        if token == "∀":
            return self._quant("forall")
        self.pop()
        if token.isdigit():
            return NatLit(token)
        if _is_name(token):
            return _resolve(token, self.bound)
        raise ParseError(token)

    def _quant(self, kind: str) -> Quant:
        self.pop()
        name = self.pop()
        if not _is_name(name):
            raise ParseError(name)
        ty = None
        if self.peek() == ":":
            self.pop()
            ty = self._iff()
        self.expect(",")
        outer = name in self.bound
        self.bound.add(name)
        body = self.expr()
        if not outer:
            self.bound.discard(name)
        return Quant(kind, name, ty, body)
