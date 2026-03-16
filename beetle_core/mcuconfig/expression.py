# Copyright © 2018-2026 Johan Cockx, Matic Kukovec & Kristof Mulier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
import re
import os
from numbers import Number, Integral, Rational
from fractions import Fraction

# Allow relative imports during stand-alone execution
import os

__package__ = __package__ or os.path.basename(os.path.dirname(__file__))
if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .error import ConfigError


class ExpressionError(ConfigError):
    pass


class UndefinedNameError(ExpressionError):
    pass


class SyntaxError(ExpressionError):
    pass


class BadTypeError(ExpressionError):
    pass


class BadIndexError(ExpressionError):
    pass


class BadWidthError(ExpressionError):
    pass


class EvalError(ExpressionError):
    pass


Value = int | Fraction | float


class Expression:
    """Base class for unsigned integer expressions.

    Concrete expressions are defined by derived classes and include literals
    (representing constant values), symbols (representing named or anonymous
    variables whose value can change) and various operators.

    Expression values are numbers. The type is computed by each derived class,
    based on the type of its arguments. The hierarchy of number types
    corresponds to Pythons Number hierarchy.

    An integral expression can optionally have a bit width. The value of an
    expression with a bit width is truncated to that number of bits. Expressions
    without bit width are never truncated.

    Expressions can be evaluated based on the current value of any symbols used
    in them.

    Expressions can be "watched", which means that a notifier function can be
    installed that gets called whenever the value of the expression changes.

    Expressions can be assigned a value, which means that any variables used in
    them will be set to achieve that value. An assignment can fail, for example
    when there are no symbols in the expression, when the algorithm used to
    implement assignments is not smart enough, or when the types do not match:
    you cannot assign a rational value to an integral expression.

    Integral expressions can be assigned with a mask, meaning that the masked
    bits are not affected by the assignment.

    Expressions can be triggered, which causes their value to be recomputed. If
    the value changed, any notifiers will be called, and dependant expressions
    will be triggered too. This is especially useful for symbols, which are the
    only expressions whose value can change due to external events (where
    "external" means "outside any expression").

    Notifiers can in turn change the value of symbols and trigger them, or
    assign a new value to an expression. To avoid an infinite cascade of
    changes, as well as notifiers that undo the changes that triggered them,
    changes are grouped in transactions.

    Within a transaction, the value of any symbol that is used is frozen. Any
    attempt to change it again within the same transaction will fail. As the
    number of frozen symbols increases monotonically, and notifiers are only
    triggered when a symbol changes, infinite loops involving notifiers cannot
    happen.

    There is a method to begin a transaction and a method to end a
    transaction. Transactions can be nested. Symbols remain frozen as long as at
    least one transaction is ongoing. Changes triggered during a transaction
    will only be processed once all changes in the current transaction are
    processed. This avoids situations where an initial change and a triggered
    change both fail due to symbols frozen by the other change.

    Assigning a value to an expression automatically begins and ends a
    transaction, as does the calling of a notifier. It is also possibly to begin
    and end a transaction explicitly.
    """

    def __init__(self):
        self._watchers = []

    width = None
    type = Number

    @property
    def value(self) -> Value:
        return self.eval()

    @property
    def mask(self) -> int:
        width = self.width
        return ~0 if width is None else _bits(width)

    def eval(self) -> Value:
        assert False, f"eval not implemented for {type(self).__name__}"

    def is_out_of_range(self, value: Value) -> bool:
        """Return true if the given value is definitely not possible.

        Return false if the value is possible or the feasibility of the value
        cannot be determined.
        """
        if not isinstance(value, self.type):
            return True
        if self.width:
            if value < 0 or value >= (1 << self.width):
                return True
        # We can refine this here,  and derived classes can refine it!
        return False

    def assign(self, value: Number, mask: int = ~0) -> bool:
        """Assign a value to an expression if possible, ignoring bits with mask
        0.

        Make sure that the value of this expression is equal to the given value.

        Return true on success, false on failure.

        Within a transaction, freeze any symbol on which the assignment relies.
        """
        # print(f"assign {truncate(self)} := {value} (0b{self.bin_format(value)})"
        #      f" width {self.width} mask {self.bin_format(mask)} ["
        # )
        assert not self.is_out_of_range(value), (
            f" value {value} out of range for {truncate(self)}"
            f" width {self.width}"
        )
        with Transaction():
            self.try_assign(value, mask)
        if mask == ~0:
            success = self.value == value
        else:
            self_value = self.value
            success = (
                False
                if self_value is None
                else self_value & mask == value & mask
            )
        # print(f"] {truncate(self)} is now {self.value} (0b{self.bin_value})")
        return success

    def try_assign(self, value: Value, mask: int = ~0) -> None:
        """Auxiliary method implementing assignment for derived classes.

        Optimizes calls.
        """
        if mask != ~0:
            mask &= self.mask
            value = self._as_int(value)
            value &= mask
        if mask:
            self._try_assign(value, mask)
            self.freeze(mask)

    def _try_assign(self, value: Value, mask: int = ~0):
        """Auxiliary method implementing assignment for derived classes.

        Try to assign the bits of value for which mask is 1 to the value of this
        expression. The necessary actions to achieve this depend on the concrete
        expression, so it is usually necessary to override this method in
        derived classes.

        Freeze any symbol used to achieve this, to make sure that the assignment
        cannot be undone within the current transaction. One way to achieve this
        is to call try_assign on all relevant subexpressions

        The default implementation keeps and freezes the current value.
        This is an appropriate implementation for literals and can
        be used as a fallback when nothing else works.

        Guarantees:
          (mask & self.mask) != 0
          if self.width is not None:
             value is an int
             (value & ~self.mask) == 0
        """
        # print(f"try_assign fallback {self} := {value} mask {mask} [")
        pass

    @property
    def symbols(self) -> Set[Symbol]:
        """Set of symbols used in this expression."""
        return {symbol for arg in self.args for symbol in arg.symbols}

    @property
    def relevant_symbols(self) -> Set[Symbol]:
        """Set of symbols relevant for the current value of this expression.

        Derived classes can be more precise. For example, for x & y, if the
        current value of x is zero, then the symbols in y are not relevant.

        In some cases, there is more than one correct answer. For example, if
        x==0 and y==0, then (x&y).relevant_symbols can be either {x} or {y}.  In
        such a case, return one of the correct answers.
        """
        return self.symbols

    @property
    def is_assignable(self) -> bool:
        return False

    def affirm(self) -> bool:
        return self.assign(1)

    @property
    def is_constant(self) -> bool:
        assert (
            self.args
        ), f"is_constant not implemented for nullary {type(self).__name__}"
        for arg in self.args:
            if not arg.is_constant:
                return False
        return True

    @property
    def constant_value(self) -> Value:
        if self.is_constant:
            return self.value
        else:
            return None

    @property
    def is_always_true(self) -> bool:
        return self.constant_value == 1

    @property
    def is_never_true(self) -> bool:
        return self.constant_value == 0

    @property
    def bin_value(self) -> str:
        return self.bin_format(self.value)

    def bin_format(self, value: Value) -> str:
        intval = self._as_int(value)
        if self.width is None:
            return f"{intval:b}"
        else:
            return f"{(intval&((1<<self.width)-1)):0{self.width}b}"

    @property
    def hex_value(self):
        return self.hex_format(self.value)

    def hex_format(self, value: Value):
        intval = self._as_int(value)
        if self.width is None:
            return f"{intval:x}"
        else:
            return f"{(intval&((1<<self.width)-1)):0{(self.width+3)//4}x}"

    @property
    def dec_value(self):
        return self.dec_format(self.value)

    def dec_format(self, value: Value):
        if self.width is None:
            return f"{value}"
        else:
            return f"{(value&((1<<self.width)-1))}#{self.width}"

    def masked(self, value: Value, mask: int):
        width = self.width
        if width is None:
            return f"{_masked(value,mask)} mask={mask}"
        else:
            return "".join(
                "x" if m == "0" else v
                for v, m in zip(f"{value:0{width}b}", f"{mask:0{width}b}")
            )

    args = []

    def watch(self, notifier: Callable[[Value], None]):
        """Register a notifier function.

        The notifier will be called whenever the value of this expression
        changes. It will be passed the new value of the expression.
        """
        if not self._watchers:
            self.watch_deps()

        class Watcher:
            def __init__(
                self,
                expression: Expression,
                notifier: Callable[[Value], None],
            ):
                self.expression = expression
                self.value = expression.value
                self.notifier = notifier

            def trigger(self, value: Value):
                if self.value != value:
                    # print(f"notify {self.expression} changed from "
                    #      f"{self.value} to {value} ["
                    # )
                    self.notifier(value)
                    # print("]")
                    self.value = value

        self._watchers.append(Watcher(self, notifier))

    def watch_and_init(
        self, notifier: Callable[[Value], None], default: Value = 0
    ):
        """Register a notifier function and call it if the current value is not
        the default value.

        This convenience method is useful when a watcher is installed to track
        any changes of the value of the expression from the default. If the
        initial value - when the watcher is installed - already deviates from
        the default, it should be reported.
        """
        self.watch(notifier)
        if self.value != default:
            notifier(self.value)

    def watch_deps(self):
        """Watch all dependencies of this expression.

        Trigger this expression when its value may have changed due to a change
        in a dependency.

        A dependency is anything that can change and will affect the value of
        this expression if it does. Examples are non-constant sub-expressions
        and any external influences on a symbol.

        This method is not intended to be called by users. It is intended to be
        overridden for symbols that have external dependencies,
        """
        for arg in self.args:
            if not arg.is_constant:
                arg.watch(lambda value: self.trigger())

    def trigger(self):
        """Report a change in value of this expression.

        Call any notifiers watching this expression immediately or at the end of
        the current transaction.
        """
        # print(f"trigger {self}")
        with Transaction():
            # print(f"trigger expression {self}")
            Expression._pending.add(self)

    _pending: set[Expression] = set()

    def process_pending():
        # print("expression process pending [")
        while Expression._pending:
            pending = Expression._pending
            Expression._pending = set()
            for expression in pending:
                # print(f"  process pending expression {expression}")
                if expression._watchers:
                    value = expression.value
                    for watcher in expression._watchers:
                        watcher.trigger(value)
        # print("]")

    @property
    def is_frozen(self) -> Bool:
        mask = self.mask
        return (self.frozen_mask & mask) == mask

    @property
    def frozen_mask(self) -> int:
        for arg in self.args:
            if not arg.is_frozen:
                return False
        return True

    def freeze(self, mask: int = ~0):
        """Freeze at least the one-bits in the mask for the current transaction.

        The default implementation freezes all bits by freezing all
        subexpressions. Derived classes can refine.
        """
        assert (
            self.args
        ), f"freeze() not implemented for nullary {type(self).__name__}"
        for arg in self.args:
            arg.freeze()

    def print_tree(self):
        print(f"print tree {truncate(self)} [")
        level = 0

        def indent():
            return "  " * level

        def sub(expression):
            nonlocal level
            prefix = f"{indent()}{type(expression).__name__}"
            value = expression.value
            bin_value = expression.bin_value
            if expression.args:
                print(f"{prefix} {value} 0b{bin_value}")
                level += 1
                for arg in expression.args:
                    sub(arg)
                level -= 1
            else:
                print(f"{prefix} {expression}: {value} 0b{bin_value}")

        sub(self)
        print(f"]")

    def _check_arg_integral(self, arg: Expression):
        if not issubclass(arg.type, Integral):
            raise BadTypeError(f"Argument of {self.opname} must be an integer")

    def _as_int(self, value: Value):
        intval = round(value)
        if self.width is not None:
            intval &= (1 << self.width) - 1
        return intval


# Abstract subclasses


class NullaryExpression(Expression):
    @property
    def args(self):
        return []


class UnaryExpression(Expression):
    def __init__(self, arg):
        self.arg = arg
        super().__init__()

    @property
    def args(self):
        return [self.arg]


class BinaryExpression(Expression):
    def __init__(self, arg1: Expression, arg2: Expression):
        self.arg1 = arg1
        self.arg2 = arg2
        super().__init__()

    @property
    def args(self):
        return [self.arg1, self.arg2]

    def __repr__(self):
        return _binary_expression_repr(self, self.arg1, self.arg2)

    @classmethod
    def join(cls, expressions: Iterable[Expression]):
        result = None
        for expression in expressions:
            if not result:
                result = expression
            else:
                result = cls(result, expression)
        if not result:
            result = cls.neutral
        return result


class PrefixExpression(UnaryExpression):
    def __repr__(self):
        return _prefix_text(self, self.arg)


class BoolBinaryExpression(BinaryExpression):
    type = int
    width = 1


class IntegralBinaryExpression(BinaryExpression):
    type = int

    def __init__(self, arg1: Expression, arg2: Expression):
        super().__init__(arg1, arg2)
        self._check_arg_integral(arg1)
        self._check_arg_integral(arg2)


class EqualWidthBinaryExpression(IntegralBinaryExpression):
    def __init__(self, arg1: Expression, arg2: Expression):
        if arg1.width and arg2.width and arg1.width != arg2.width:
            raise BadWidthError(
                f"unequal width {arg1.width} (for '{arg1}') "
                f"and {arg2.width} (for '{arg2}')"
                f" for '{self.opname}'"
            )
        super().__init__(arg1, arg2)

    @property
    def width(self):
        return self.arg1.width or self.arg2.width


class Symbol(NullaryExpression):
    """A base class for symbols.

    Deriving from Symbol simplifies the implementation of custom symbols in
    expressions. Specifically,  it provides a default implementation of
    'is_constant' and 'is_assignable', as well as a default implementation of
    'try_assign' that relies on simpler 'update' method.

    Derived classes must provide an 'eval' method as well as either an 'update'
    method or a 'try_assign' method ('update' recommended). They can provide a
    type property.

    eval(self) -> Value

    Return the current value of the symbol

    update(self, value: int, mask: int)

    Update the value of the symbol to 'value' for bits that are set in 'mask',
    keeping the other bits.

    type -> type

    Return the type of the value returned by this expression, Defaults to Value.
    Must be a supertype of type(eval(self)) .
    """

    @property
    def is_constant(self) -> bool:
        return False

    @property
    def is_assignable(self) -> bool:
        return True

    def update(self, value: Value, mask: int = ~0):
        """Update the value of this symbol, without triggering side effects.

        Side effects of the change will be triggered automatically when the
        current transaction ends.
        """
        assert False, f"update not implemented for {type(self).__name__}"

    @property
    def symbols(self) -> Set[Symbol]:
        return {self}

    def freeze(self, mask: int = ~0):
        # print(f"freeze {self} at {self.masked(self.value, mask)}")
        Transaction.freeze(self, mask)

    @property
    def frozen_mask(self) -> int:
        return Transaction.frozen_mask(self)

    def _try_assign(self, value: Value, mask: int = ~0):
        # print(
        #    f"try_assign symbol {self} := {value}"
        #    f" (from {self.value}) mask {mask} ["
        # )
        with Transaction():
            Transaction.update(self, value, mask)
            self.freeze(mask)
        # print("]")


# Concrete subclasses


class Literal(NullaryExpression):
    def __init__(self, value: Value, width: Optional[int] = None):
        assert width is None or isinstance(
            value, Integral
        ), f"non-integral literal {value} cannot have width {width}"
        assert width is None or width > 0, width
        assert width is None or value >= 0, f"{value}#{width}"
        assert width is None or value < (
            1 << width
        ), f"literal {value} is too big for width {width}"
        self._value = value
        self.width = width
        super().__init__()

    @property
    def type(self) -> type:
        return type(self._value)

    def eval(self) -> Value:
        return self._value

    @property
    def is_constant(self) -> bool:
        return True

    @property
    def frozen_mask(self) -> int:
        return ~0

    def freeze(self, mask: int = ~0):
        pass

    def __repr__(self):
        if self.width is None:
            return f"{self._value}"
        else:
            return f"0b{self._value:0{self.width}b}"


Never = Literal(value=0, width=1)
Always = Literal(value=1, width=1)


class BitSelect(UnaryExpression):
    opname = "["

    def __init__(self, arg: Expression, msb: int, lsb: int):
        assert lsb >= 0, lsb
        assert msb >= lsb
        assert (
            arg.width is None or msb < arg.width
        ), f"msb {msb} too big for arg width {arg.width}"
        super().__init__(arg)
        self._offset = lsb
        self._width = msb - lsb + 1
        self._check_arg_integral(arg)

    @property
    def type(self) -> type:
        return int

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def width(self) -> int:
        return self._width

    def eval(self) -> int:
        return _keep(self.arg.value >> self.offset, self.width)

    def _try_assign(self, value: Value, mask: int = ~0):
        # print(f"BitSelect {self.arg} [{self.offset+self.width-1}:{self.offset}] "
        #      f":= {self.masked(value,mask)} ["
        # )
        self.arg.try_assign(
            value=(value & self.mask) << self.offset,
            mask=(mask & self.mask) << self.offset,
        )

    # print("]")

    def freeze(self, mask: int = ~0):
        self.arg.freeze((mask & self.mask) << self.offset)

    @property
    def frozen_mask(self) -> int:
        return _keep(self.arg.frozen_mask >> self.offset, self.width)

    @property
    def is_assignable(self) -> bool:
        return self.arg.is_assignable()

    @property
    def args(self):
        return [self.arg]

    def __repr__(self):
        if self.width == 1:
            return f"{self.arg}[{self.offset}]"
        else:
            return f"{self.arg}[{self.offset+self.width-1}:{self.offset}]"


class Equal(BoolBinaryExpression):
    opname = "=="

    def eval(self) -> int:
        return int(self.arg1.eval() == self.arg2.eval())

    def _try_assign(self, value: Value, mask: int = ~0):
        # print(f"Equal {self} := {value} mask {mask} [")
        if mask & 1:
            if value & 1:
                self.arg1.try_assign(self.arg2.value)
                self.arg2.try_assign(self.arg1.value)
                # print("] success")
                return
            else:
                width = self.arg1.width or self.arg2.width
                if width:
                    arg2 = self.arg2.value
                    for v in range(1 << width):
                        if v != arg2:
                            self.arg1.try_assign(v, ~0)
                            if self.arg1.value != self.arg2.value:
                                # print(f"] success with arg1 := {v}")
                                return
                    arg1 = self.arg1.value
                    for v in range(1 << width):
                        if v != arg1:
                            self.arg2.try_assign(v, ~0)
                            if self.arg1.value != self.arg2.value:
                                # print(f"] success with arg2 := {v}")
                                return
        # print("] nothing to do")


class Less(BoolBinaryExpression):
    opname = "<"

    # Todo: check at construction that args are Real, not Complex
    # Currently, we do not have syntax for complex numbers in expressions,
    # so this is not urgent.

    def eval(self) -> int:
        return int(self.arg1.value < self.arg2.value)

    def __repr__(self):
        if _swap_comparison_args(self.arg1, self.arg2):
            return _binary_expression_repr(More, self.arg2, self.arg1)
        return _binary_expression_repr(self, self.arg1, self.arg2)


class Not(PrefixExpression):
    opname = "~"
    type = int

    def __init__(self, arg: Expression):
        super().__init__(arg)
        self._check_arg_integral(arg)

    @property
    def width(self):
        return self.arg.width

    def __init__(self, arg: Expression):
        super().__init__(arg)
        self._check_arg_integral(arg)

    def eval(self) -> int:
        if self.arg.width is None:
            return ~self.arg.value
        else:
            return _keep(~self.arg.value, self.arg.width)

    def _try_assign(self, value: Value, mask: int = ~0):
        intval = self._as_int(value)
        # print(f"Not {self.arg} := {intval} mask {mask} [")
        self.arg.try_assign(~intval, mask)
        # print("]")

    def freeze(self, mask: int = ~0):
        self.arg.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        return self.arg.frozen_mask

    @property
    def is_assignable(self) -> bool:
        return self.arg.is_assignable

    def __repr__(self):
        if self.width == 1:
            if type(self.arg) is Less:
                if _swap_comparison_args(self.arg.arg1, self.arg.arg2):
                    return _binary_expression_repr(
                        NotMore, self.arg.arg2, self.arg.arg1
                    )
                else:
                    return _binary_expression_repr(
                        NotLess, self.arg.arg1, self.arg.arg2
                    )
            if type(self.arg) is Equal:
                return _binary_expression_repr(
                    NotEqual, self.arg.arg1, self.arg.arg2
                )
            return _prefix_text(LogicalNot, _strip_not_zero(self.arg))
        return super().__repr__()


class And(EqualWidthBinaryExpression):
    opname = "&"

    def eval(self) -> int:
        # print(f"    eval And {self}: {self.arg1.value & self.arg2.value}")
        return self.arg1.value & self.arg2.value

    def _try_assign(self, value: int, mask: int = ~0):
        # print(f"And({self.arg1} , {self.arg2}) := {self.masked(value,mask)} [")
        intval = self._as_int(value)
        with Transaction() as t:
            self.arg1.try_assign(intval, mask & (intval | self.arg2.value))
            self.arg2.try_assign(intval, mask & (intval | self.arg1.value))
            if self.value & mask == intval & mask:
                # print("] success A")
                return
            # print("] rollback")
            t.rollback()
            # print("[")
            self.arg2.try_assign(intval, mask & (intval | self.arg1.value))
            self.arg1.try_assign(intval, mask & (intval | self.arg2.value))
            if self.value & mask == intval & mask:
                # print("] success B")
                return
            t.rollback()
        # print(f"] fail")

    neutral = Literal(~0)

    @property
    def relevant_symbols(self) -> Set[Symbol]:
        if self.width != 1 or self.value:
            return super().relevant_symbols
        arg = self.arg2 if not self.arg2.value else self.arg1
        return arg.relevant_symbols

    def freeze(self, mask: int = ~0):
        mask &= ~self.frozen_mask
        if mask:
            self.arg1.freeze(mask)
            self.arg2.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        frozen1 = self.arg1.frozen_mask
        frozen2 = self.arg2.frozen_mask
        return (
            (frozen1 & frozen2)
            | (frozen1 & ~self.arg1.value)
            | (frozen2 & ~self.arg2.value)
        )

    def __repr__(self):
        if self.width == 1:
            return _binary_expression_repr(
                LogicalAnd,
                _strip_not_zero(self.arg1),
                _strip_not_zero(self.arg2),
            )
        return super().__repr__()


class Xor(EqualWidthBinaryExpression):
    opname = "^"

    def eval(self) -> int:
        return self.arg1.value ^ self.arg2.value

    def _try_assign(self, value: int, mask: int = ~0):
        intval = self._as_int(value)
        self.arg1.try_assign(intval ^ self.arg2.value, mask)
        self.arg2.try_assign(intval ^ self.arg1.value, mask)

    neutral = Literal(0)

    def freeze(self, mask: int = ~0):
        self.arg1.freeze(mask)
        self.arg2.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        return self.arg1.frozen_mask & self.arg2.frozen_mask


class Or(EqualWidthBinaryExpression):
    opname = "|"

    def eval(self) -> int:
        # print(f"    eval Or {self}: {self.arg1.value | self.arg2.value}")
        return self.arg1.value | self.arg2.value

    def _try_assign(self, value: int, mask: int = ~0):
        # print(f"Or a1: {self.arg1} a2: {self.arg2} := {value} mask {mask} [")
        intval = self._as_int(value)
        with Transaction() as t:
            self.arg1.try_assign(intval, mask & ~(intval & self.arg2.value))
            self.arg2.try_assign(intval, mask & ~(intval & self.arg1.value))
            if self.value & mask == intval & mask:
                # print("] success A")
                return 0
            t.rollback()
            self.arg2.try_assign(intval, mask & ~(intval & self.arg1.value))
            self.arg1.try_assign(intval, mask & ~(intval & self.arg2.value))
            if self.value & mask == intval & mask:
                # print("] success B")
                return 0
            t.rollback()
        # print(f"] fail")

    neutral = Literal(0)

    @property
    def relevant_symbols(self) -> Set[Symbol]:
        if self.width != 1 or not self.value:
            return super().relevant_symbols
        arg = self.arg2 if self.arg2.value else self.arg1
        return arg.relevant_symbols

    def freeze(self, mask: int = ~0):
        mask &= ~self.frozen_mask
        if mask:
            self.arg1.freeze(mask)
            self.arg2.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        frozen1 = self.arg1.frozen_mask
        frozen2 = self.arg2.frozen_mask
        return (
            (frozen1 & frozen2)
            | (frozen1 & self.arg1.value)
            | (frozen2 & self.arg2.value)
        )


class Concat(IntegralBinaryExpression):
    opname = ":"

    def __init__(self, arg1: Expression, arg2: Expression):
        super().__init__(arg1, arg2)
        if arg1.width is None or arg2.width is None:
            raise BadWidthError(f"Cannot concatenate expressions without width")

    @property
    def width(self):
        return self.arg1.width + self.arg2.width

    def eval(self) -> int:
        return (self.arg1.value << self.arg2.width) | self.arg2.value

    def _try_assign(self, value: Value, mask: int = ~0):
        # print(f"Concat({self.arg1} , {self.arg2}) := "
        #      f"{self.masked(value,mask)} ["
        # )
        intval = self._as_int(value)
        self.arg1.try_assign(intval >> self.arg2.width, mask >> self.arg2.width)
        self.arg2.try_assign(
            _keep(intval, self.arg2.width), _keep(mask, self.arg2.width)
        )
        # print("]")

    def freeze(self, mask: int = ~0):
        self.arg1.freeze(mask >> self.arg2.width)
        self.arg2.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        return (
            self.arg1.frozen_mask << self.arg2.width
        ) | self.arg2.frozen_mask

    @property
    def is_assignable(self) -> bool:
        return self.arg1.is_assignable and self.arg2.is_assignable


class Add(BinaryExpression):
    opname = "+"

    width = None

    @property
    def type(self) -> type:
        if issubclass(self.arg1.type, Integral) and issubclass(
            self.arg2.type, Integral
        ):
            return Integral
        return super().type

    def eval(self) -> Value:
        return _add(self.arg1.value, self.arg2.value)

    def _try_assign(self, value: Value, mask: int = ~0):
        self.arg1.try_assign(_add(value, -self.arg2.value), mask)
        self.arg2.try_assign(_add(value, -self.arg1.value), mask)

    neutral = Literal(0)

    def __repr__(self):
        if type(self.arg2) is Minus:
            return _binary_expression_repr(Subtract, self.arg1, self.arg2.arg)
        return super().__repr__()


class Minus(PrefixExpression):
    opname = "-"

    width = None

    @property
    def type(self) -> type:
        return self.arg.type

    def eval(self) -> Value:
        return -self.arg.value

    def _try_assign(self, value: Value, mask: int = ~0):
        self.arg.try_assign(-value, mask)


class Multiply(BinaryExpression):
    opname = "*"

    width = None

    @property
    def type(self) -> type:
        if issubclass(self.arg1.type, Integral) and issubclass(
            self.arg2.type, Integral
        ):
            return Integral
        return super().type

    def eval(self) -> Value:
        return _multiply(self.arg1.value, self.arg2.value)

    def _try_assign(self, value: Value, mask: int = ~0):
        value2 = self.arg2.value
        if value2:
            self.arg1.try_assign(_divide(value, value2))
        else:
            self.arg1.freeze()
        value1 = self.arg1.value
        if value1:
            self.arg2.try_assign(_divide(value, value1))
        else:
            self.arg2.freeze()

    neutral = Literal(1)


class Divide(BinaryExpression):
    opname = "/"

    width = None

    def eval(self) -> Value:
        value2 = self.arg2.value
        if not value2:
            # raise EvalError("Divide by zero")
            return 0
        return _divide(self.arg1.value, value2)

    def _try_assign(self, value: Value, mask: int = ~0):
        value2 = self.arg2.value
        if value2:
            self.arg1.try_assign(_multiply(value, value2))
        else:
            self.arg1.freeze()
        if value:
            value1 = self.arg1.value
            if value1:
                self.arg2.try_assign(_divide(value1, value))
            else:
                self.arg2.freeze()


class Fixed(UnaryExpression):
    opname = "fixed"

    @property
    def type(self) -> type:
        return self.arg.type

    def eval(self) -> Value:
        return self.arg.eval()

    def _try_assign(self, value: Value, mask: int = ~0):
        self.freeze()

    def freeze(self, mask: int = ~0):
        self.arg.freeze(mask)

    @property
    def frozen_mask(self) -> int:
        return self.arg.frozen_mask

    def __repr__(self):
        return f"{self.opname}({self.arg})"


_builtins = {builtin.opname: builtin for builtin in [Fixed]}

# Virtual subclasses


class More(BoolBinaryExpression):
    opname = ">"

    def __new__(cls, arg1: Expression, arg2: Expression):
        return Less(arg2, arg1)


class NotLess(BoolBinaryExpression):
    opname = ">="

    def __new__(cls, arg1: Expression, arg2: Expression):
        return LogicalNot(Less(arg1, arg2))


class NotMore(BoolBinaryExpression):
    opname = "<="

    def __new__(cls, arg1: Expression, arg2: Expression):
        return LogicalNot(More(arg1, arg2))


class NotEqual(BoolBinaryExpression):
    opname = "!="

    def __new__(cls, arg1: Expression, arg2: Expression):
        return LogicalNot(Equal(arg1, arg2))


class LogicalNot(PrefixExpression):
    opname = "!"

    def __new__(cls, arg: Expression):
        return Not(_to_bool(arg))


class LogicalAnd(BoolBinaryExpression):
    opname = "&&"

    def __new__(cls, arg1: Expression, arg2: Expression):
        return And(_to_bool(arg1), _to_bool(arg2))


class LogicalOr(BoolBinaryExpression):
    opname = "||"

    def __new__(cls, arg1: Expression, arg2: Expression):
        return Or(_to_bool(arg1), _to_bool(arg2))


class Subtract(EqualWidthBinaryExpression):
    opname = "-"

    def __new__(cls, arg1: Expression, arg2: Expression):
        return Add(arg1, Minus(arg2))


def _strip_not_zero(arg):
    if type(arg) is Not and type(arg.arg) is Equal:
        if type(arg.arg.arg2) is Literal and arg.arg.arg2.value == 0:
            return arg.arg.arg1
        if type(arg.arg.arg1) is Literal and arg.arg.arg1.value == 0:
            return arg.arg.arg2
    return arg


def _to_bool(arg):
    return arg if arg.width == 1 else NotEqual(arg, Literal(0, arg.width))


class Transaction:
    """A transaction changes each symbol at most once and can be undone.

    During a transaction:
        - every symbol can be changed at most once
        - the original value of each symbol is remembered
        - it is possible to rollback all changes
        - actions triggered by changes are postponed

    A rollback restores the changes made during the transaction, unfreezes
    symbols and discards pending actions created during the transaction.

    Transactions can be nested.  A change made in a parent transaction cannot be
    undone in a nested transaction.

    A commit of a nested transaction adds the original values and pending
    actions to the parent transaction.

    A commit of the top level transaction executes pending actions and discards
    original values, in that order.  In other words, during triggered actions,
    changed values remain frozen, original values can be consulted, and
    additional changes are added to the top level transaction.

    Usage:

        with Transaction() as transaction:
           ...assign values to expressions + freeze symbols...
           ...optionally: transaction.rollback()
           ...repeat as desired until ready to commit
    """

    # Current transaction, or None
    _current: Optional["Transaction"] = None

    def __enter__(self):
        # print("transaction [")
        self._parent = Transaction._current
        Transaction._current = self
        # For each change in this transaction, this dict contains a (value,mask)
        # pair where mask is set for bits that have been saved in this or a
        # parent transaction, and value contains the saved value for saved bits
        # and is undefined for other bits.
        self._saved: dict[Symbol, (int, int)] = {}
        return self

    def rollback(self):
        # print("rollback")
        for symbol, (value, mask) in self._saved.items():
            symbol.update(value, mask)
        self._saved = {}

    def __exit__(self, *args):
        # print("transaction [")
        assert Transaction._current is self
        if self._parent:
            self._add_saved_to_parent()
        else:
            # print(f"exit root transaction [")
            # print("process pending")
            Expression.process_pending()
            # print("] exit root transaction")
        Transaction._current = self._parent
        # print("] transaction")

    def freeze(symbol: Symbol, mask: int = ~0):
        """Freeze the symbol's value at the 1 bits of the mask.

        Symbol remains frozen during the current transaction.
        """
        if Transaction._current:
            Transaction._current._freeze(symbol, mask)

    def update(symbol: Symbol, value: Value, mask: int = ~0):
        """Update and freeze the symbol's value at the 1 bits of the mask.

        Ignore 1 bits in the mask that have been previously frozen. Save the old
        value of the bits,  so that rollback can restore them.
        """
        assert Transaction._current
        Transaction._current._update(symbol, value, mask)

    def frozen_mask(symbol: Symbol) -> int:
        """Return a mask with 1 bits for bits frozen in any active
        transaction."""
        return (
            Transaction._current._frozen_mask(symbol)
            if Transaction._current
            else 0
        )

    def _frozen_mask(self, symbol: Symbol) -> int:
        return self._get(symbol)[1]

    def _freeze(self, symbol: Symbol, mask: int = ~0):
        # print(f"### freeze {symbol} at {symbol.value} mask={mask}")
        self._save(symbol, symbol.value, mask)
        assert not mask & ~self._frozen_mask(symbol)

    def _update(self, symbol: Symbol, value: Value, mask: int = ~0):
        # print(f"### update {symbol} := {value} mask={mask}")
        mask = self._save(symbol, symbol.value, mask)
        if mask:
            symbol.update(value, mask)
            symbol.trigger()

    def _add_saved_to_parent(self):
        for symbol, (value, mask) in self._saved.items():
            # print(f"### commit {symbol}")
            self._parent._save(symbol, value, mask)

    def _get(self, symbol: Symbol):
        transaction = self
        while transaction:
            value_mask_pair = transaction._saved.get(symbol)
            if value_mask_pair:
                return value_mask_pair
            transaction = transaction._parent
        return (0, 0)

    def _save(self, symbol: Symbol, value: Value, mask: int) -> int:
        # Method can becalled to save a value before setting a new value, or to
        # freeze it, or to propagate it up from a nested transaction. Probably
        # not a good place for debug printing.
        old_value, old_mask = self._get(symbol)
        mask &= ~old_mask
        if mask:
            # print(f"### save {symbol} := {value} mask={mask}"
            #      f" from {old_value} mask {old_mask}"
            # )
            self._saved[symbol] = (
                (
                    value
                    if mask == ~0
                    else (value & mask) | (old_value & old_mask)
                ),
                mask | old_mask,
            )
        return mask


_operators_by_precedence = [
    # List operators grouped by precedence, highest precedence first.
    [Not, LogicalNot, Minus],
    [Multiply, Divide],
    [Add, Subtract],
    [Less, More, NotLess, NotMore],
    [Equal, NotEqual],
    [And],
    [Xor],
    [Or],
    [LogicalAnd],
    [LogicalOr],
    [Concat],
]


def _init_operator_precedence():
    Expression.precedence = len(_operators_by_precedence)
    for precedence, operators in enumerate(reversed(_operators_by_precedence)):
        for operator in operators:
            operator.precedence = precedence


_init_operator_precedence()

_operator_by_opname = {
    operator.opname: operator
    for operators in _operators_by_precedence
    for operator in operators
}

_binary_opnames = [
    operator.opname
    for operators in _operators_by_precedence
    for operator in operators
    if issubclass(operator, BinaryExpression)
]

_binary_operator_regex = "|".join(
    re.escape(opname)
    for opname in sorted(_binary_opnames, key=len, reverse=True)
)
"""A symbol lookup function returns the symbol with a given name, or None if
there is no such symbol, or raises an UndefinedName exception in case of other
issues."""
type SymbolLookupFunction = Callable[[str], Optional[Expression]]


def parse(
    text: str, lookup: SymbolLookupFunction = lambda x: None
) -> Expression:
    todo = text
    tried = False

    def take(regex: str) -> str | None:
        nonlocal todo
        nonlocal tried
        match = re.match(regex, todo)
        if not match:
            tried = True
            return
        result = todo[0 : match.end()]
        todo = todo[match.end() :]
        tried = False
        return result

    def skip_space() -> None:
        take(r"[ \t]*")

    def expect(regex) -> None:
        skip_space()
        if not take(regex):
            raise SyntaxError(f"missing '{regex.replace('\\','')}'")

    def take_name() -> str | None:
        return take(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)*")

    def take_symbol() -> Expression | None:
        name = take_name()
        if not name:
            return None
        symbol = lookup(name)
        if symbol:
            return symbol
        builtin = take_builtin(name)
        if builtin:
            return builtin
        raise UndefinedNameError(f"undefined name '{name}'")

    def take_uint() -> Expression | None:
        value_text = take(r"(0x[0-9a-fA-F]+|0b[01]+|[0-9]+)(?![A-Fa-f0-9_])")
        if value_text is None:
            return
        scale = 1
        if take("k"):
            scale = 1024
        elif take("M"):
            scale = 1024 * 1024
        elif take("G"):
            scale = 1024 * 1024 * 1024
        if take("#"):
            width_text = take(r"[0-9]+")
            if width_text is None:
                raise BadWidthError(
                    f"missing width after '{value_text}#' in '{text}'"
                )
            width = int(width_text)
        elif value_text[1:2] == "b":
            width = len(value_text) - 2
        elif value_text[1:2] == "x":
            width = (len(value_text) - 2) * 4
        else:
            width = None
        return Literal(value=int(value_text, base=0) * scale, width=width)

    def take_builtin(name: str) -> Expression | None:
        builtin = _builtins.get(name)
        if builtin:
            expect(r"\(")
            arg = take_expression()
            if not arg:
                raise SyntaxError(f"missing expression for '{name}(...)'")
            expect(r"\)")
            return builtin(arg)

    def take_atomic_expression() -> Expression | None:
        symbol = take_symbol()
        if symbol:
            skip_space()
            if take(r"\["):
                skip_space()
                msb = take_uint().value
                skip_space()
                if take(":"):
                    lsb = take_uint().value
                else:
                    lsb = msb
                expect("]")
                if msb < lsb:
                    raise BadIndexError(f"{msb} < {lsb} in '{text}'")
                if msb >= symbol.width:
                    raise BadIndexError(f"{msb} >= {symbol.width} in '{text}'")
                return BitSelect(arg=symbol, msb=msb, lsb=lsb)
            else:
                return symbol
        literal = take_uint()
        if literal is not None:
            return literal
        if take(r"\("):
            skip_space()
            value = take_expression()
            expect(r"\)")
            return value

    def take_prefix_expression() -> Expression | None:
        opname = take("~|!|-")
        if opname:
            skip_space()
            arg = take_prefix_expression()
            if not arg:
                raise SyntaxError(f"missing expression after '{opname}'")
            operator = _operator_by_opname[opname]
            assert issubclass(operator, PrefixExpression)
            return operator(arg)
        return take_atomic_expression()

    def take_binary_expression(binary_operator_regex) -> Expression | None:
        arg1 = take_prefix_expression()
        if arg1:
            while True:
                skip_space()
                opname = take(binary_operator_regex)
                if not opname:
                    break
                operator = _operator_by_opname[opname]
                skip_space()
                arg2 = take_binary_expression(operator.binary_arg_regex)
                if not arg2:
                    raise SyntaxError(f"missing expression after '{opname}'")
                arg1 = operator(arg1, arg2)
            return arg1

    def take_binary_operator() -> type | None:
        opname = take(_binary_operator_regex)
        if not opname:
            return None
        return _operator_by_opname[opname]

    def take_expression() -> Expression | None:

        # Take the longest possible expression with precedence higher than the
        # given precedence, plus the following operator, if any.  Return them as
        # a pair.
        # Note: "higher than" implements left-associativity, "not lower than"
        # would implement right-associativity.
        def take_subexpression(
            precedence: int,
        ) -> (Expression | None, type | None):
            arg1 = take_prefix_expression()
            if not arg1:
                return None, None
            skip_space()
            operator = take_binary_operator()
            while True:
                if not operator or operator.precedence <= precedence:
                    return arg1, operator
                skip_space()
                arg2, next_operator = take_subexpression(operator.precedence)
                if not arg2:
                    raise SyntaxError(
                        f"missing expression after '{operator.opname}'"
                    )
                arg1 = operator(arg1, arg2)
                operator = next_operator

        expression, operator = take_subexpression(-1)
        assert not operator, operator
        return expression

    try:
        skip_space()
        expression = take_expression()
        if expression is None or todo:
            if take(r"{"):
                name = take_name()
                if name is None:
                    raise SyntaxError(f"parameter name expected after '{{'")
                raise UndefinedNameError(f"unknown parameter name '{name}'")
            raise SyntaxError(f"unexpected character or syntax error")
        assert isinstance(
            expression, Expression
        ), f"unexpected type {type(expression).__name__} parsed from '{text}'"
    except ExpressionError as error:
        near = f" near '{todo}'" if todo and tried else ""
        error.args = (f"{error}{near} in expression '{text}'",)
        raise error from None

    return expression


def truncate(data):
    text = str(data)
    max = 1000
    if len(text) <= max:
        return text
    ellipsis = "..."
    text = text[: max - len(ellipsis)] + ellipsis
    open = 0
    for c in text:
        if c == "(":
            open += 1
        elif c == ")":
            open -= 1
    while open > 0:
        open -= 1
        text += ")"
    return text


def _bits(width: int, offset: int = 0):
    return ((1 << width) - 1) << offset


def _keep(value: int, width: int, offset: int = 0):
    return value & _bits(width, offset)


def _drop(value: int, width: int, offset: int = 0):
    return value & ~_bits(width, offset)


def _invert(value: int, width: int) -> int:
    return ~value & _bits(width)


def _masked(value: Value, mask: int = ~0) -> Value:
    if isinstance(value, Integral):
        return value & mask
    assert mask == ~0, mask
    return value


def _add(x: Value, y: Value) -> Value:
    return _simplify(x + y)


def _multiply(x: Value, y: Value) -> Value:
    return _simplify(x * y)


def _divide(x: Value, y: Value) -> Value:
    if isinstance(x, Integral) and isinstance(y, Integral):
        if x % y == 0:
            return x // y
        return Fraction(x, y)
    return _simplify(x / y)


def _simplify(value: Value) -> Value:
    if isinstance(value, Fraction) and value.denominator == 1:
        return value.numerator
    return value


def _arg_text(arg: Expression, minimum_precedence: int) -> str:
    if arg.precedence < max(minimum_precedence, And.precedence):
        return f"({arg})"
    else:
        return f"{arg}"


def _prefix_text(
    operator: Union[Expression, type],
    arg: Expression,
) -> str:
    return f"{operator.opname}{_arg_text(arg, operator.precedence)}"


def _binary_expression_repr(
    operator: Union[Expression, type],
    arg1: Expression,
    arg2: Expression,
) -> str:
    # Assume left associativity: add one to precedence for arg2
    arg1_text = _arg_text(arg1, operator.precedence)
    arg2_text = _arg_text(arg2, operator.precedence + 1)
    return f"{arg1_text} {operator.opname} {arg2_text}"


def _swap_comparison_args(arg1: Expression, arg2: Expression):
    return type(arg1) is Literal and not type(arg2) is Literal


def selftest():
    print("Selftest for expression")
    print(f"Binary opnames: {' '.join(_binary_opnames)}")
    print(f"Binary operator regex: {_binary_operator_regex}")

    print("operators by precedence:")
    for level, operators in reversed(
        list(enumerate(reversed(_operators_by_precedence)))
    ):
        print(
            f"{level}: {' '.join(operator.__name__ for operator in operators)}"
        )

    assert parse("64k").value == 1 << 16

    symbols = dict()

    class Variable(Symbol):
        type = int

        def __init__(self, name, address, offset, width, value):
            print(f"create {name} at {address} {offset}+{width} := {value}")
            self.name = name
            self.address = address
            self.offset = offset
            self.width = width
            super().__init__()
            self._value = value
            symbols[name] = self

        def eval(self) -> int:
            return self._value

        def update(self, value: int, mask: int = ~0):
            # print(f"update {self} := {self.masked(value,mask} [")
            print(f"# set {self} := {value} mask {mask}")
            assert value < (1 << self.width), f"overflow: {value}#{self.width}"
            self._value = (value & mask) | (self._value & ~mask)
            actual = self._value
            assert (
                actual & mask == value & mask
            ), f"expected {value}, got {actual}"
            # print(f"] {self} is now {self.value}")

        def __repr__(self):
            return self.name

    # Address 8888888877777777
    # Offset  7654321076543210
    # ALL     0000000000000000
    # FOO              110
    # BAR_OFF             1110
    # FLAG      1
    # MAP     00

    ALL = Variable(
        "ALL", address=7, offset=0, width=16, value=0b0010000001101110
    )
    FOO = Variable("FOO", address=7, offset=4, width=3, value=6)
    BAR_OFF = Variable("BAR.OFF", address=7, offset=0, width=4, value=14)
    FLAG = Variable("FLAG", address=8, offset=5, width=1, value=1)
    MAP = Variable("MAP", address=8, offset=7, width=2, value=0)
    BOB = Variable("BOB", address=9, offset=7, width=3, value=0)

    assert Variable("W5", 10, 0, 5, 0).masked(9, 24) == "01xxx"

    def lookup(name):
        return symbols.get(name)

    assert ALL == parse("ALL", lookup)
    assert ALL.value == 0b0010000001101110, f"{ALL.value:0{ALL.width}b}"

    foo_is_five = parse("FOO == 5", lookup)
    foo_is_five.assign(1)
    assert foo_is_five.value == 1, foo_is_five.value
    assert parse("FOO", lookup).value == 5
    parse("FOO", lookup).assign(6)

    class Expr(Expression):
        def __init__(self, text):
            super().__init__(text, lookup)

    def test(expression_text: str, expect: Union[int, type], expect_width=None):
        try:
            expression = parse(expression_text, lookup)
            value = expression.value
            width = expression.width
        except ExpressionError as error:
            if expect == type(error):
                print(f"correct: '{expression_text}' => {type(error).__name__}")
                return
            raise error
        if value != expect:
            raise ValueError(
                f"'{expression}' evaluates to {value} ({bin(value)})"
                f" instead of {expect} ({bin(expect)})"
            )
        if width != expect_width:
            raise ValueError(
                f"'{expression}' width is {width} instead of {expect_width}"
            )
        print(f"correct: '{expression_text}' => {expression} => {value}")
        assert parse(str(expression), lookup).value == expression.value, (
            f"{expression_text} -> {expression.eval()}   "
            f"{str(expression)} -> {parse(str(expression), lookup).eval()}"
        )

    test("", SyntaxError)
    test("FOO", 6, 3)
    test("FOOL", UndefinedNameError)
    test("FOO[1", SyntaxError)
    test("FOO[1:2]", BadIndexError)
    test("FOO[5:1]", BadIndexError)
    test("FOO[2:1]", 3, 2)
    test("BAR.OFF", 14, 4)
    test("17", 17)
    test("0", 0)
    test("1", 1)
    test("0xa", 10, 4)
    test("0xag", SyntaxError)
    test("17#5", 17, 5)
    test("17#xxx", BadWidthError)
    test("0xf : FOO ", 0b1111110, 7)
    test("0xf : FOO : FOOL", UndefinedNameError)
    test("0xf:FOO:BAR.OFF ", 0b11111101110, 11)
    test("(0b0011 | 0b0101) : 0b01", 0b011101, 6)
    test("(0b00 : 0b11) | 0b0101", 0b0111, 4)
    test("~FOO", 1, 3)
    test("(FOO & ~BAR.OFF[3:1]) == 1  ", 0, 1)
    test("(FOO) == 0 || (FOO) == 2", 0, 1)
    test("FLAG & FOO==0b110", 1, 1)
    test("FOO < 7", 1, 1)
    test("FOO < 6", 0, 1)
    test("FOO > 7", 0, 1)
    test("FOO > 5", 1, 1)
    test("6 <= 5", 0, 1)
    test("FOO <= 5", 0, 1)
    test("FOO <= 6", 1, 1)
    test("FOO >= 6", 1, 1)
    test("FOO >= 7", 0, 1)
    test("FOO == 6", 1, 1)
    test("FOO == 7", 0, 1)
    test("FOO != 6", 0, 1)
    test("FOO != 7", 1, 1)
    test("MAP == 0b00 || MAP == 0b10 || MAP == 0b01", 1, 1)
    # test("ALL[5:3,1,0]", 22, 5)
    test("1/0", 0)
    test("1/0+1", 1)

    def assign(name, value):
        print(f"assign {name} := {value}")
        lookup(name).assign(value)

    def change(text, expression, value):
        print(f"{text} changed to {value} {value:0{expression.width}b}")
        nonlocal change_count
        change_count += 1

    def watch(text):
        print(f"watch {text}")
        expression = parse(text, lookup)
        expression.watch(lambda value: change(text, expression, value))

    change_count = 0
    watch("FOO")
    assert change_count == 0, change_count
    assign("FOO", 5)
    assert change_count == 1, change_count
    watch("FOO > 4")
    watch("ALL")
    assert change_count == 1, change_count
    assign("FOO", 4)
    assert change_count == 3, change_count

    predicate = parse("((FOO[2:1]:BAR.OFF[2:0]) & 0b11000) == 0b01000", lookup)
    assert predicate.value == 0, f"{predicate} is {predicate.value} not 0"
    print(f"assign {predicate} := 1")
    predicate.assign(1)
    assert predicate.value == 1, f"{predicate} is {predicate.value} not 1"

    print("\ncheck side effects")
    BAR_OFF.watch_and_init(lambda x: FOO.assign(x & 7))
    print(f"FOO={FOO.value} BAR.OFF={BAR_OFF.value}")
    assert (
        FOO.value == BAR_OFF.value & 7
    ), f"FOO={FOO.value} BAR.OFF={BAR_OFF.value}"
    assert BAR_OFF.assign(2)
    assert BAR_OFF.value == 2
    assert (
        FOO.value == BAR_OFF.value & 7
    ), f"FOO={FOO.value} BAR.OFF={BAR_OFF.value}"

    print("\ncheck freezing during side effects")
    print(f"MAP == {MAP.value}")
    assert MAP.value == 0
    MAP.watch(lambda value: MAP.assign(0))
    # An assignment should succeed, even if a side-effect tries to override it
    assert MAP.assign(1)
    # A side-effect should not override the original assignment
    assert MAP.value == 1

    print("\ncheck that second change within a transaction fails")
    print(f"FLAG = {FLAG.value}")
    assert FLAG.value == 1
    with Transaction():
        assert FLAG.assign(0)
        assert FLAG.value == 0
        assert not FLAG.assign(1)
        assert FLAG.value == 0
    assert FLAG.value == 0

    print("\ncheck: a nested transaction in a pending action must not unfreeze")

    def reset_flag(value):
        with Transaction():
            pass
        FLAG.assign(0)

    FLAG.watch(reset_flag)
    assert FLAG.assign(1)
    assert FLAG.value == 1

    print("\ncheck multiplication and subtraction")
    assert FLAG.assign(0)
    x = parse("(2 - FLAG) * 8", lookup)
    assert x.value == 16, x.value
    assert x.assign(8)
    assert FLAG.value == 1

    print("\ncheck fixed builtin")
    assert FLAG.assign(1)
    assert MAP.assign(2)
    x = parse("fixed(MAP) * FLAG", lookup)
    assert x.value == 2, x.value
    assert x.assign(0)
    assert MAP.value == 2
    assert FLAG.value == 0

    print("\ncheck backtracking")
    FLAG.assign(0)
    expr = parse("(!FLAG & 0) | FLAG", lookup)
    # Should: set FLAG=0, fail, set FLAG=1
    # Only works if FLAG is not frozen after fail
    expr.assign(1)
    assert FLAG.value, expr.print_tree()

    print("\ncheck symbol extraction")
    expr = parse("((FOO[2:1]:BAR.OFF[2:0]) & 0b11000) == 0b01000", lookup)
    assert expr.symbols == {FOO, BAR_OFF}
    assert parse("7", lookup).symbols == set()

    print("\ncheck side effects")
    print("when BAR_OFF changes,  also change FOO which changes BOB [")

    def on_BAR_OFF(value: int):
        FOO.assign(value & 7)

    def on_FOO(value: int):
        BOB.assign(value)

    BAR_OFF.watch_and_init(on_BAR_OFF)
    FOO.watch_and_init(on_FOO)
    print(f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}")
    assert (
        FOO.value == BAR_OFF.value & 7
    ), f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}"
    assert (
        BOB.value == FOO.value
    ), f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}"
    print("]")
    print("assign BAR_OFF := 2 and check that FOO is also changed [")
    assert BAR_OFF.assign(2)
    print(f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}")
    assert BAR_OFF.value == 2
    assert (
        FOO.value == BAR_OFF.value & 7
    ), f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}"
    assert (
        BOB.value == FOO.value
    ), f"BAR.OFF={BAR_OFF.value} FOO={FOO.value} BOB={BOB.value}"
    print("]")

    print("Selftest for expression succeeded")


if __name__ == "__main__":
    selftest()
