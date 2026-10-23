# kickmix Python API notes

Auto-generated from the built module docstrings.

## Circuit
```
An immutable kickmix circuit.

Examples:
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     X q0
    ...     CX q0 q9
    ... ''')

    >>> simulator = km.Simulator(batch_size=1)
    >>> print(simulator.read_within_shot(km.q(9), shot_index=0))
    False
    >>> simulator.do(circuit)
    >>> print(simulator.read_within_shot(km.q(9), shot_index=0))
    True
```

## CircuitBuilder
```
A builder class that helps create a kickmix circuit.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()

    >>> target = builder.create_quantum_register(7, "target")
    >>> shift = builder.create_quantum_register(2, "shift")
    >>> builder.left_rotate(target, shift)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -target[0]-SWAP-------------SWAP-------------SWAP-----------
                   |                |                |
    q1: -target[1]-SWAP-------------|----------------|----SWAP------
                   |                |                |    |
    q2: -target[2]-|----SWAP--------SWAP-------------|----|---------
                   |    |           |                |    |
    q3: -target[3]-|----|----SWAP---|----SWAP--------|----SWAP------
                   |    |    |      |    |           |    |
    q4: -target[4]-|----|----|------|----|----SWAP---SWAP-|---------
                   |    |    |      |    |    |      |    |
    q5: -target[5]-|----|----SWAP---|----|----SWAP---|----|----SWAP-
                   |    |    |      |    |    |      |    |    |
    q6: -target[6]-|----SWAP-|------|----SWAP-|------|----|----SWAP-
                   |    |    |      |    |    |      |    |    |
    q7: -shift[0]--@----@----@----@-|----|----|----@-|----|----|----
                                  | |    |    |    | |    |    |
    q8: -shift[1]-----------------X-@----@----@----X-@----@----@----
```

## GF2Field
```
A binary extension field GF(2^m) with polynomial basis arithmetic.

Elements are polynomials of degree less than m over GF(2), represented
in Python as non-negative integers where bit k is the coefficient of x^k.
Addition is bitwise XOR, and multiplication is polynomial multiplication
reduced modulo an irreducible polynomial of degree m.

Examples:
    >>> import kickmix as km
    >>> field = km.GF2Field(4)
    >>> field.degree
    4
    >>> hex(field.modulus)
    '0x13'
    >>> field.primitive_element
    2
    >>> field.mul(3, 5)
    15
```

## OperationStatistics
```
Operation count statistics from a `km.Circuit` or `km.Simulator`.

Acts as a read-only mapping from base operation name (`'X'`,
`'CX'`, `'CCX'`, `'Z_POW'`, etc.) to count, so `stats['X']`,
`stats.get('X')`, `'X' in stats`, `dict(stats)`, `stats.keys()`,
`stats.values()`, and `stats.items()` all work directly. Also
provides resource helpers (`num_instructions`, `num_toffoli_like`,
`num_t_like`, `num_z_pow`, and `z_pow_clifford_hierarchy_counts`).

Examples:
    >>> import kickmix as km
    >>> c = km.Circuit('''
    ...     X q0
    ...     CCX q0 q1 q2
    ...     Z_POW q0 0.25
    ... ''')
    >>> stats = c.operation_statistics()
    >>> stats.num_toffoli_like, stats.num_t_like, stats['X']
    (1, 1, 1)
    >>> dict(stats)['CCX']
    1
```

## Simulator
```
An interactive kickmix simulator.
```

## UnaryIterationCursor
```
A cursor that steps through values of an address register.

Create a cursor with `builder.unary_iteration(address, ...)` and open a pass
using a `with` block. Inside the block, iterate with a `for` loop to visit
`(address_value, match_qubit)` pairs in order, or call `move_to` to jump to
any value.

Entering the `with` block allocates `max(1, len(address))` temporary qubits;
leaving the block uncomputes and frees them. A cursor that is never opened
adds no operations to the circuit, and the same cursor can be reused across
multiple `with` blocks.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(2, name='address')
    >>> target = builder.create_quantum_register(1, name='target')
    >>> cursor = builder.unary_iteration(address)
    >>> with cursor:
    ...     for address_value, match_qubit in cursor:
    ...         if address_value == 3:
    ...             builder.cx(match_qubit, target[0])
    >>> # Reusing the same cursor to uncompute:
    >>> with cursor:
    ...     for address_value, match_qubit in cursor:
    ...         if address_value == 3:
    ...             builder.cx(match_qubit, target[0])
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.use_same_registers_as(circuit)
    >>> for a in range(4):
    ...     sim.write_within_shot('address', a, a)
    >>> sim.do(circuit)
    >>> for a in range(4):
    ...     print(f"{a}: {sim.read_within_shot('target', a, out=int)}")
    0: 0
    1: 0
    2: 0
    3: 0
```

## array
```
An immutable array of qubit ids, bit ids, and/or boolean values.

Circuit creation methods operate substantially faster when given a
km.array,  rather than a normal python list of values, because a
km.array's values are stored contiguously in memory alongside compressed
type information.

Examples:
    >>> import kickmix as km
    >>> arr = km.array([km.q(0), km.b(1), True])
    >>> arr
    km.array([km.q(0), km.b(1), True])
    >>> len(arr)
    3
```

## b
```
A kickmix bit index.
```

## q
```
A kickmix qubit index.
```

## r
```
A kickmix register index.
```

## xb
```
A kickmix bit index being interpreted as an X basis value.

X basis values act like controls when given as the targets
of bit flip operations. For example, cx(BitId(0), XBitId(1)) is equivalent
to cz(BitId(0), BitId(1)).

Examples:
    >>> import kickmix as km
    >>> x = km.xb(5)
    >>> x.id
    5
```

## xbool
```
A boolean that represents an X basis value.

If the boolean is True, the X basis value is |->.
If the boolean is False, the X basis value is |+>.

X basis values act like controls when given as the targets
of bit flip operations. For example, cx(a, xbool(b)) is equivalent
to cz(a, b).

Examples:
    >>> import kickmix as km
    >>> km.xbool(True)
    km.xbool(True)
    >>> bool(km.xbool(False))
    False
    >>> bool(km.xbool(True))
    True
```

## Circuit.flame_chart_svg
```
flame_chart_svg(self: kickmix.Circuit) -> str

@signature def flame_chart_svg(self) -> str:
Returns a flame chart of qubits and operations in the circuit.

In order for this method to work, the circuit must be annotated with
"@enter:subroutine" and "@exit:subroutine" INFO_TAG instructions. If
the circuit isn't annotated, the chart will be very boring.

Returns:
    An SVG string containing the flame chart.

Examples:
    >>> import tempfile
    >>> import kickmix as km

    >>> builder = km.CircuitBuilder()
    >>> a = builder.create_quantum_register(3, "a")
    >>> b = builder.create_quantum_register(3, "b")
    >>> c = builder.create_quantum_register(3, "c")

    >>> builder.info_tag("@enter:big_cswap")
    >>> builder.cx(b, a)
    >>> builder.ccx(c, a, b)
    >>> builder.cx(b, a)
    >>> builder.info_tag("@exit:big_cswap")
    >>> builder.iadd(offset=a, target=b)

    >>> circuit = builder.finish_circuit()
    >>> svg = circuit.flame_chart_svg()
    >>> 'big_cswap' in svg
    True
    >>> 'iadd' in svg
    True
    >>> with tempfile.NamedTemporaryFile() as fp:
    ...     with open(fp.name, 'w') as f:
    ...         print(circuit.flame_chart_svg(), file=f)
```

## Circuit.from_file
```
from_file(path: object, format: str = 'auto') -> kickmix.Circuit

@signature def from_file(path: str | pathlib.Path | io.IOBase, format: Literal['auto', 'kmx', 'kmb'] = 'auto') -> km.Circuit:
Reads a `km.Circuit` from a file.

Args:
    path: The path or open file object to read from.
    format: The file format to parse. Defaults to `'auto'`.
        `'auto'`: Automatically detect whether the file is in `'kmx'`
            or `'kmb'` format.
        `'kmx'`: Human-readable text kickmix format. Can be read from
            a text or binary file. See
            https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_format.md
        `'kmb'`: Binary kickmix format. Requires a binary file if
            passing an open file object. See
            https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md

Returns:
    The parsed `km.Circuit`.

Examples:
    >>> import pathlib
    >>> import tempfile
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     CCX q0 q1 q2
    ...     CX q0 q1
    ...     X q0
    ... ''')
    >>> with tempfile.TemporaryDirectory() as d:
    ...     path = pathlib.Path(d) / 'circuit.kmx'
    ...     circuit.to_file(path)
    ...     loaded = km.Circuit.from_file(path)
    >>> loaded == circuit
    True
```

## Circuit.html_diagram
```
html_diagram(self: kickmix.Circuit) -> str

@signature def html_diagram(self) -> str:
Returns an html diagram of the circuit.

Examples:
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     X q0
    ...     CX q0 q1
    ... ''')
    >>> html = circuit.html_diagram()
    >>> '<html' in html
    True
```

## Circuit.num_bits
```
Returns the number of bits used by the circuit.
```

## Circuit.num_qubits
```
Returns the number of qubits used by the circuit.
```

## Circuit.num_registers
```
Returns the number of registers used by the circuit.
```

## Circuit.operation_statistics
```
operation_statistics(self: kickmix.Circuit) -> kickmix.OperationStatistics

@signature def operation_statistics(self) -> km.OperationStatistics:
Counts how many times operations are mentioned by the circuit.

Beware that this method ignores the fact that operations mentioned
by the circuit may only occur in a fraction of runs. For example,
suppose a classical bit determines whether an addition is performed
(via `PUSH_CONDITION` and `POP_CONDITION`) and then the inverse of
that bit determines whether a subtraction is performed. Even
though, in a given run, only the addition or else only the
subtraction can occur, this method will return operation counts as
if both occurred.

Returns:
    A `km.OperationStatistics` object containing operation counts
    and resource summaries (`num_instructions`, `num_toffoli_like`,
    `num_t_like`, `num_z_pow`, and
    `z_pow_clifford_hierarchy_counts`).

Examples:
    >>> import kickmix as km
    >>> c = km.Circuit('''
    ...     X q0
    ...     CCX q0 q1 q2 if b0
    ...     Z_POW q0 0.5
    ...     Z_POW q0 0.25
    ...     Z_POW q0 -0.25 if b0
    ...     Z_POW q0 0.125
    ... ''')
    >>> stats = c.operation_statistics()
    >>> stats.num_toffoli_like, stats.num_t_like
    (1, 2)
    >>> stats.num_z_pow(min_clifford_hierarchy_level=4)
    1
    >>> stats['X'], stats['Z_POW']
    (1, 4)
```

## Circuit.reaction_depth
```
reaction_depth(self: kickmix.Circuit) -> int

@signature def reaction_depth(self) -> int:
Returns the reaction depth of the circuit, assuming it is powered by
CCZ states.

Examples:
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     CCX q0 q1 q2
    ...     CCX q2 q3 q4
    ... ''')
    >>> circuit.reaction_depth()
    2
```

## Circuit.register_data
```
@signature def register_data(self) -> dict[str | km.r, km.array]:
The names and contents of registers in the circuit, as a dict.

Examples:
    >>> import kickmix as km

    >>> circuit = km.Circuit('''
    ...     REGISTER r0 "test"
    ...     APPEND_TO_REGISTER q0 r0
    ...     APPEND_TO_REGISTER q1 r0
    ...     APPEND_TO_REGISTER q2 r0
    ...     REGISTER r2 "empty"
    ...     REGISTER r3
    ...     APPEND_TO_REGISTER q3 r3
    ...     APPEND_TO_REGISTER b0 r3
    ...     CCX q0 q1 q2
    ...     CX q0 q1
    ...     X q0
    ... ''')
    >>> data: dict[str | km.r, km.array] = circuit.register_data
    >>> for k, v in data.items():
    ...     print(f"{k!r}: {v!r}")
    'test': km.array([km.q(0), km.q(1), km.q(2)])
    km.r(1): km.array([])
    'empty': km.array([])
    km.r(3): km.array([km.q(3), km.b(0)])
```

## Circuit.text_diagram
```
text_diagram(self: kickmix.Circuit) -> str

@signature def text_diagram(self) -> str:
Returns a text diagram of the circuit.

Examples:
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     X q0
    ...     CX q0 q1
    ...     CCX q0 q1 q2
    ... ''')
    >>> print(circuit.text_diagram())
    q0: -X-@-@-
           | |
    q1: ---X-@-
             |
    q2: -----X-
```

## Circuit.to_file
```
to_file(self: kickmix.Circuit, path: object, format: str = 'kmx') -> None

@signature def to_file(self, path: str | pathlib.Path | io.IOBase, format: Literal['kmx', 'kmb'] = 'kmx') -> None:
Writes the circuit to a file.

Args:
    path: The path or open file object to write to.
    format: The file format to write. Defaults to `'kmx'`.
        `'kmx'`: Human-readable text kickmix format. Can be written
            to a text or binary file. See
            https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_format.md
        `'kmb'`: Binary kickmix format. Requires a binary file if
            passing an open file object. See
            https://github.com/quantumlib/Qualtran/blob/main/docs/kickmix/kickmix_binary_format.md

Examples:
    >>> import pathlib
    >>> import tempfile
    >>> import kickmix as km
    >>> circuit = km.Circuit('''
    ...     CCX q0 q1 q2
    ...     CX q0 q1
    ...     X q0
    ... ''')
    >>> with tempfile.TemporaryDirectory() as d:
    ...     path = pathlib.Path(d) / 'circuit.kmb'
    ...     circuit.to_file(path, format='kmb')
    ...     loaded = km.Circuit.from_file(path, format='kmb')
    >>> loaded == circuit
    True
```

## CircuitBuilder.alloc_bits
```
alloc_bits(self: kickmix.CircuitBuilder, count: int) -> kickmix.array

Allocates classical bits to use as workspace in a circuit.

Allocated bits can be deallocated with the `km.CircuitBuilder.free` method.

Args:
    count: The number of classical bits to allocate.

Returns:
    An array containing the ids of the allocated bits. Until these ids
    are freed, they won't be returned by any other allocation calls.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> b = builder.alloc_bits(3)
    >>> b
    km.array([km.b(0), km.b(1), km.b(2)])
    >>> builder.free(b)
```

## CircuitBuilder.alloc_qubits
```
alloc_qubits(self: kickmix.CircuitBuilder, count: int) -> kickmix.array

Allocates clean qubits to use as workspace in a circuit.

Allocated qubits can be deallocated with the `km.CircuitBuilder.free` method.

If the allocation would push `km.CircuitBuilder.num_allocated_qubits` above
`km.CircuitBuilder.max_qubits` (which defaults to infinity), it will raise
an exception instead of returning a result.

Although the qubits returned by this method *should* be clean, nothing
*enforces* this. If a prior user of the allocated qubits failed to
correctly clean some qubits before freeing them, the returned qubits may
contain their buggy garbage. As such, it's recommended that you reset
the qubits before using them. Reset gates also have the nice side effect
of clearly indicating in circuit diagrams when a new usage of a qubit
has begun.

Args:
    count: The number of qubits to allocate.

Returns:
    An array containing the ids of the allocated qubits. Until these ids
    are freed, they won't be returned by any other allocation calls.

Raises:
    ValueError:
        Attempted to allocate more qubits than the maximum (if set).
        See also `km.CircuitBuilder.num_free_qubits`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> q = builder.alloc_qubits(3)
    >>> q
    km.array([km.q(0), km.q(1), km.q(2)])
    >>> builder.num_allocated_qubits
    3
```

## CircuitBuilder.bit_store
```
bit_store(self: kickmix.CircuitBuilder, target: object, value: object, *, control: object = True) -> None

@signature def bit_store(self, target: km.b | km.array, value: bool, *, control: km.b | bool | km.array = True) -> None:
Appends operations to perform `if control: target = value`.

Writes a constant into classical bits. The control must be
classical, since a classical bit cannot be coherently conditioned
on a qubit.

This method broadcasts over km.array arguments.

Args:
    target: The classical bit (or bits) to write into.
    value: The constant to store.
    control: Defaults to True. Determines if the store occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> a = builder.create_classical_register(1, name='a')[0]
    >>> b = builder.create_classical_register(1, name='b')[0]
    >>> out = builder.create_classical_register(1, name='out')[0]
    >>> # Compute logical OR: out = a | b
    >>> builder.bit_store(out, False)
    >>> builder.bit_store(out, True, control=km.array([a, b]))
    >>> builder.finish_circuit()
    km.Circuit('''
        APPEND_TO_REGISTER b0 r0
        REGISTER r0 "a"
        APPEND_TO_REGISTER b1 r1
        REGISTER r1 "b"
        APPEND_TO_REGISTER b2 r2
        REGISTER r2 "out"
        BIT_STORE0 b2
        BIT_STORE1 b2 if b0
        BIT_STORE1 b2 if b1
    ''')
```

## CircuitBuilder.ccx
```
ccx(self: kickmix.CircuitBuilder, control1: object, control2: object, target: object) -> None


            @signature def ccx(self, control1: bool | km.b | km.q | km.array, control2: bool | km.b | km.q | km.array, target: km.q | km.array) -> None:
            Appends many doubly-controlled NOT gates to the circuit.

            This method broadcasts over km.array arguments. If any of the arguments is a
            km.array, an append is performed for each array index. When multiple km.array
            arguments are used, they are combined by zipping (i.e. using two arrays of
            length n will produce n instructions rather than n*n instructions).

            The exact kind of operation(s) appended to the circuit depends on the types of
            the controls. For example, if one of the controls is the boolean value True
            instead of a qubit, then a CX instruction will be appended instead of a CCX
            instruction.

            Args:
                control1: One of the controls determining if the NOT gate happens or not.
                control2: The other control determining if the NOT gate happens or not.
                target: The qubit to bit flip when the controls are satisfied.

            Examples:
                >>> import kickmix as km

                >>> # Demo a simple ccx call
                >>> builder = km.CircuitBuilder()
                >>> builder.ccx(km.q(0), km.q(1), km.q(2))
                >>> builder.finish_circuit()
                km.Circuit('''
                    CCX q0 q1 q2
                ''')

                >>> # Demo a broadcasting call
                >>> builder = km.CircuitBuilder()
                >>> shared_control = builder.create_quantum_register(1, "shared_control")[0]
                >>> controls = builder.create_quantum_register(3, "controls")
                >>> targets = builder.create_quantum_register(3, "targets")[0]
                >>> builder.ccx(shared_control, controls, targets)
                >>> builder.finish_circuit()
                km.Circuit('''
                    APPEND_TO_REGISTER q0 r0
                    REGISTER r0 "shared_control"
                    APPEND_TO_REGISTER q1 r1
                    APPEND_TO_REGISTER q2 r1
                    APPEND_TO_REGISTER q3 r1
                    REGISTER r1 "controls"
                    APPEND_TO_REGISTER q4 r2
                    APPEND_TO_REGISTER q5 r2
                    APPEND_TO_REGISTER q6 r2
                    REGISTER r2 "targets"
                    CCX q0 q1 q4
                    CCX q0 q2 q4
                    CCX q0 q3 q4
                ''')
```

## CircuitBuilder.ccz
```
ccz(self: kickmix.CircuitBuilder, control1: object, control2: object, control3: object) -> None

@signature def ccz(self, control1: bool | km.b | km.q | km.array, control2: bool | km.b | km.q | km.array, control3: bool | km.b | km.q | km.array) -> None:
Appends many CCZ gates to the circuit.

This method broadcasts over km.array arguments. If any of the arguments
is a km.array, an append is performed for each array index. When
multiple km.array arguments are used, they are combined by zipping
(i.e. using two arrays of length n will produce n instructions rather
than n*n instructions).

The exact kind of operation(s) appended to the circuit depends on the
types of the controls. For example, if one of the controls is the
boolean value True instead of a qubit, then a CZ instruction will be
appended instead of a CCZ instruction.

Args:
    control1: The first control determining if phasing occurs.
    control2: The second control determining if phasing occurs.
    control3: The third control determining if phasing occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.ccz(km.q(0), km.q(1), km.q(2))
    >>> builder.finish_circuit()
    km.Circuit('''
        CCZ q0 q1 q2
    ''')
```

## CircuitBuilder.create_classical_register
```
create_classical_register(self: kickmix.CircuitBuilder, length: int, name: str) -> kickmix.array

Creates a classical register.

Reserves the given number of bits for the register, and emits
instructions defining the register.

Args:
    length: The number of bits in the register.
    name: A name for the register, which can be used to refer to it.

Returns:
    A km.array containing the allocated bits.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> reg = builder.create_classical_register(2, name='meas')
    >>> reg
    km.array([km.b(0), km.b(1)])
    >>> builder.bit_store(reg[0], True)
    >>> builder.finish_circuit()
    km.Circuit('''
        APPEND_TO_REGISTER b0 r0
        APPEND_TO_REGISTER b1 r0
        REGISTER r0 "meas"
        BIT_STORE1 b0
    ''')
```

## CircuitBuilder.create_quantum_register
```
create_quantum_register(self: kickmix.CircuitBuilder, length: int, name: str) -> kickmix.array

Creates a quantum register.

Reserves the given number of qubits for the register, and emits
instructions defining the register.

Args:
    length: The number of qubits in the register.
    name: A name for the register, which can be used to refer to it.

Returns:
    A km.array containing the allocated qubits.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> reg = builder.create_quantum_register(2, name='data')
    >>> reg
    km.array([km.q(0), km.q(1)])
    >>> builder.x(reg[0])
    >>> builder.finish_circuit()
    km.Circuit('''
        APPEND_TO_REGISTER q0 r0
        APPEND_TO_REGISTER q1 r0
        REGISTER r0 "data"
        X q0
    ''')
```

## CircuitBuilder.cswap
```
cswap(self: kickmix.CircuitBuilder, control: object, target1: object, target2: object) -> None

@signature def cswap(self, control: bool | km.b | km.q | km.array, target1: km.q | km.array, target2: km.q | km.array) -> None:
Appends controlled-SWAP (Fredkin) gates to the circuit.

Performs `if control: target1, target2 = target2, target1`.
This method broadcasts over km.array arguments.

The cost depends on the control. A qubit control emits a CSWAP
instruction (costing one Toffoli) per index. A classical bit control
emits a classically-conditioned SWAP instruction, costing no Toffolis.
A control of True reduces to a plain SWAP, and False emits nothing.

Args:
    control: Determines if the swap happens.
    target1: The first qubit or register to swap.
    target2: The second qubit or register to swap.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> c = builder.create_quantum_register(1, name='c')[0]
    >>> x = builder.create_quantum_register(2, name='x')
    >>> y = builder.create_quantum_register(2, name='y')
    >>> builder.cswap(c, x, y)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -c[0]-@----@----
              |    |
    q1: -x[0]-SWAP-|----
              |    |
    q2: -x[1]-|----SWAP-
              |    |
    q3: -y[0]-SWAP-|----
                   |
    q4: -y[1]------SWAP-
```

## CircuitBuilder.cx
```
cx(self: kickmix.CircuitBuilder, control: object, target: object) -> None

@signature def cx(self, control: bool | km.b | km.q | km.array, target: km.q | km.b | km.xb | km.xbool | km.array) -> None:
Appends controlled-NOT gates (or classical/phase equivalents) to the circuit.

This method broadcasts over `km.array` and sequence arguments. When
multiple array arguments are given, they are combined by zipping.

The exact instruction(s) emitted depend on the types of `control`
and `target`. For example, a qubit control and qubit target emit
`CX`; a classical bit control and qubit target emit `X_IF`; a
classical bit control and classical bit target emit `BIT_INVERT_IF`;
and an X-basis target (`km.xb` or `km.xbool`) converts the operation
into a phase flip (such as `Z_IF` or `Z`).

Args:
    control: The control (qubit, bit, bool, or array) determining
        if the target is flipped.
    target: The target (qubit, bit, X-basis bit/bool, or array) to
        flip when `control` is active.

Raises:
    ValueError: Broadcast array lengths do not match, or `control`
        and `target` have incompatible types (such as a qubit
        control with a classical bit target).

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.cx(km.q(0), km.q(1))
    >>> builder.cx(km.b(0), km.q(1))
    >>> builder.cx(True, km.q(1))
    >>> builder.finish_circuit()
    km.Circuit('''
        CX q0 q1
        X q1 if b0
        X q1
    ''')
```

## CircuitBuilder.cz
```
cz(self: kickmix.CircuitBuilder, control1: object, control2: object) -> None

@signature def cz(self, control1: bool | km.b | km.q | km.array, control2: bool | km.b | km.q | km.array) -> None:
Appends many CZ gates to the circuit.

This method broadcasts over km.array arguments. If any of the arguments
is a km.array, an append is performed for each array index. When
multiple km.array arguments are used, they are combined by zipping
(i.e. using two arrays of length n will produce n instructions rather
than n*n instructions).

The exact kind of operation(s) appended to the circuit depends on the
types of the controls. For example, if one of the controls is the
boolean value True instead of a qubit, then a Z instruction will be
appended instead of a CZ instruction.

Args:
    control1: One of the controls determining if phasing occurs.
    control2: The other controls determining if phasing occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.cz(km.q(0), km.q(1))
    >>> builder.finish_circuit()
    km.Circuit('''
        CZ q0 q1
    ''')
```

## CircuitBuilder.debug_print
```
debug_print(self: kickmix.CircuitBuilder, arg: object) -> None

@signature def debug_print(self, arg: km.q | km.b | bool | km.xb | km.xbool | km.array | Sequence[km.q | km.b | bool | km.xb | km.xbool]) -> None:
Appends DEBUG_PRINT instructions to print the given values during simulation.

Emits a `DEBUG_PRINT` instruction for each item in `arg`, followed
by an empty `DEBUG_PRINT` instruction (which ends the debug output
line).

Args:
    arg: The qubit, bit, boolean, or array/sequence of values to
        print.

Raises:
    TypeError: `arg` cannot be converted to printable kickmix items.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.debug_print([km.q(0), km.b(1)])
    >>> builder.finish_circuit()
    km.Circuit('''
        DEBUG_PRINT q0
        DEBUG_PRINT b1
        DEBUG_PRINT
    ''')
```

## CircuitBuilder.del_and
```
del_and(self: kickmix.CircuitBuilder, control1: object, control2: object, target: object) -> None

@signature def del_and(self, control1: bool | km.b | km.q | km.array, control2: bool | km.b | km.q | km.array, target: km.q | km.array) -> None:
Clears a qubit holding `control1 and control2` using stabilizer operations.

This is the uncomputation partner of `init_and`, or of a `ccx` into
a qubit that started at |0>. It applies an `HMR` (X-basis
measurement and Z-basis reset to |0>) to `target`, followed by a
phase correction `CZ(control1, control2)` conditioned on the
measurement result being 1. The `target` qubit is left in |0> and is
not freed, so the caller still decides when to `free` it.

This method broadcasts over km.array arguments.

Args:
    control1: One of the controls that was used to compute the target.
    control2: The other control that was used to compute the target.
    target: The qubit holding the AND, restored to |0>.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> c1 = builder.alloc_qubits(1)[0]
    >>> c2 = builder.alloc_qubits(1)[0]
    >>> target = builder.alloc_qubits(1)[0]
    >>> builder.del_and(c1, c2, target)
    >>> builder.finish_circuit()
    km.Circuit('''
        HMR q2 b0
        CZ q0 q1 if b0
    ''')
```

## CircuitBuilder.del_gf2_div
```
del_gf2_div(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, field: object = None) -> None

@signature def del_gf2_div(self, lhs: km.array, rhs: km.array, *, target: km.array, field: km.GF2Field | None = None) -> None:
Clears a GF(2^m) register known to hold `(lhs / rhs) % modulus` to 0.

This is the uncomputation partner of `init_gf2_div`. Temporary
workspace is allocated to recompute the inverse. If you still hold
the scaffold from `init_gf2_div_with_scaffold`, use
`del_gf2_div_with_scaffold` instead to avoid the recompute.

Args:
    lhs: The dividend register. Left unchanged.
    rhs: The divisor register. Left unchanged.
    target: The register holding `lhs / rhs`, cleared to 0.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(8, name='lhs')
    >>> rhs = builder.create_quantum_register(8, name='rhs')
    >>> quotient = builder.init_gf2_div(lhs, rhs)
    >>> builder.del_gf2_div(lhs, rhs, target=quotient)
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like  # 135 to build, 108 to rebuild
    243
```

## CircuitBuilder.del_gf2_div_with_scaffold
```
del_gf2_div_with_scaffold(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, scaffold: object, field: object = None) -> None

@signature def del_gf2_div_with_scaffold(self, lhs: km.array, rhs: km.array, *, target: km.array, scaffold: km.array, field: km.GF2Field | None = None) -> None:
Clears `target` and its scaffold, using only Cliffords and measurement.

This is the uncomputation partner of `init_gf2_div_with_scaffold`.
Because the divisor's inverse is still live, both `target` and
`scaffold` are cleared to 0 without any Toffolis. Neither register
is freed, so the caller still decides when to `free` them.

Args:
    lhs: The dividend register. Left unchanged.
    rhs: The divisor register. Left unchanged.
    target: The register holding `lhs / rhs`, cleared to 0.
    scaffold: The workspace from `init_gf2_div_with_scaffold`, also
        cleared to 0.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(8, name='lhs')
    >>> rhs = builder.create_quantum_register(8, name='rhs')
    >>> quotient, scaffold = builder.init_gf2_div_with_scaffold(lhs, rhs)
    >>> builder.del_gf2_div_with_scaffold(
    ...     lhs, rhs, target=quotient, scaffold=scaffold)
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like  # no more than building it once
    135
```

## CircuitBuilder.del_gf2_inverse
```
del_gf2_inverse(self: kickmix.CircuitBuilder, input: object, *, target: object, field: object = None) -> None

@signature def del_gf2_inverse(self, input: km.array, *, target: km.array, field: km.GF2Field | None = None) -> None:
Clears `target` (holding `input ** -1` in GF(2^m)) back to 0.

This is the uncomputation partner of `init_gf2_inverse`. Temporary
workspace is allocated to rebuild and uncompute the addition chain.
If you still hold the scaffold from
`init_gf2_inverse_with_scaffold`, use
`del_gf2_inverse_with_scaffold` instead to avoid the rebuild.

Args:
    input: The inverted GF(2^m) register. Left unchanged.
    target: The register holding `input ** -1`, cleared to 0.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> inp = builder.create_quantum_register(8, name='inp')
    >>> inv = builder.init_gf2_inverse(inp)
    >>> builder.del_gf2_inverse(inp, target=inv)
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like  # 108 to build, 108 to rebuild
    216
```

## CircuitBuilder.del_gf2_inverse_with_scaffold
```
del_gf2_inverse_with_scaffold(self: kickmix.CircuitBuilder, input: object, *, target: object, scaffold: object, field: object = None) -> None

@signature def del_gf2_inverse_with_scaffold(self, input: km.array, *, target: km.array, scaffold: km.array, field: km.GF2Field | None = None) -> None:
Clears `target` and its scaffold, using only Cliffords and measurement.

This is the uncomputation partner of
`init_gf2_inverse_with_scaffold`. Because the addition chain is
still live, both `target` and `scaffold` are cleared to 0 without
any Toffolis. Neither register is freed, so the caller still
decides when to `free` them.

Args:
    input: The inverted GF(2^m) register. Left unchanged.
    target: The register holding `input ** -1`, cleared to 0.
    scaffold: The addition chain from
        `init_gf2_inverse_with_scaffold`, also cleared to 0.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> inp = builder.create_quantum_register(8, name='inp')
    >>> inv, scaffold = builder.init_gf2_inverse_with_scaffold(inp)
    >>> builder.del_gf2_inverse_with_scaffold(
    ...     inp, target=inv, scaffold=scaffold)
    >>> stats = builder.finish_circuit().operation_statistics()
    >>> stats.num_toffoli_like  # no more than building it once
    108
```

## CircuitBuilder.del_gf2_mul
```
del_gf2_mul(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, field: object = None, control: object = True) -> None

@signature def del_gf2_mul(self, lhs: km.array, rhs: km.array, *, target: km.array, field: km.GF2Field | None = None, control: km.q | km.b | bool = True) -> None:
Clears a GF(2^m) register known to hold `(lhs * rhs) % modulus`.

This is the uncomputation partner of `init_gf2_mul`. When
uncontrolled, uncomputes `target` back to 0 using X-basis
measurements and classically conditioned CZ fixups (zero Toffolis).

Args:
    lhs: The first factor register. Left unchanged.
    rhs: The second factor register. Left unchanged.
    target: The GF(2^m) register holding `lhs * rhs`, cleared to 0.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.
    control: Defaults to True. Determines if the operation occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(1, name='lhs')
    >>> rhs = builder.create_quantum_register(1, name='rhs')
    >>> target = builder.init_gf2_mul(lhs, rhs)
    >>> builder.del_gf2_mul(lhs, rhs, target=target)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -lhs[0]-@--------@-----
                |        |
    q1: -rhs[0]-@--------Z**b0-
                |
    q2:  |0>----X-HMR=b0
```

## CircuitBuilder.del_lookup
```
del_lookup(self: kickmix.CircuitBuilder, *, table: object, address: object, target: object) -> None

@signature def del_lookup(self, *, table: Iterable[int], address: km.array, target: km.array) -> None:
Appends operations to perform `del target := table[address]`.

Clears a value created by looking up a value from a classical table,
indexed by a quantum register.

Because this is a `del` method, the target qubits will end in the 0
state.

Args:
    table: The table of classical values, as a list of python integers.
        The integers are interpreted in a little-endian fashion, meaning
        that `table_data[address, out_index] ==
        (table[address] >> out_index) & 1`.
    address: The address used to select a value from the table.
        Qubits are in little-endian order.
    target: The qubits to clear the lookup result from.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(2, name='address')
    >>> target = builder.create_quantum_register(4, name='target')
    >>> table = [2, 3, 5, 7]
    >>> builder.init_lookup(table=table, address=address, target=target)
    >>> builder.del_lookup(table=table, address=address, target=target)
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.use_same_registers_as(circuit)
    >>> for a in range(4):
    ...     sim.write_within_shot('address', a, a)
    >>> sim.do(circuit)
    >>> [sim.read_within_shot('target', a, out=int) for a in range(4)]
    [0, 0, 0, 0]
```

## CircuitBuilder.finish_circuit
```
finish_circuit(self: kickmix.CircuitBuilder) -> kickmix.Circuit

Returns the circuit built by the circuit builder.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.x(km.q(0))
    >>> builder.cx(km.q(0), km.q(1))
    >>> builder.finish_circuit()
    km.Circuit('''
        X q0
        CX q0 q1
    ''')
```

## CircuitBuilder.flip_if_equal
```
flip_if_equal(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, control: object = True) -> None

@signature def flip_if_equal(self, lhs: km.array, rhs: km.array | int, *, target: km.q, control: km.q | km.b | bool = True) -> None:
Appends operations to perform `if control: target ^= lhs == rhs`.

Xors the result of an unsigned integer comparison into a target qubit.

Args:
    lhs: The little-endian value on the left hand side of the comparison.
    rhs: The little-endian value or non-negative integer constant on the
        right hand side of the comparison.
    target: The qubit to flip when lhs == rhs.
    control: Defaults to True. Determines if the comparisons happens at all.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> t = builder.create_quantum_register(1, name='t')[0]
    >>> a = builder.create_quantum_register(2, name='a')
    >>> builder.flip_if_equal(a, 2, target=t)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -t[0]-------------X-------------------------------
                          |
    q1: -a[0]-X-----@-----|---------------------Z**b0-X---
                    |     |
    q2: -a[1]-X-X---|---@-@--------Z**b0--------------X-X-
                    |   | |        |
    q3:         |0>-X---@-|--------@-----HMR=b0
                        | |
    q4:             |0>-X-@-HMR=b0
    >>> # Quantum-quantum comparison:
    >>> builder = km.CircuitBuilder()
    >>> t = builder.create_quantum_register(1, name='t')[0]
    >>> a = builder.create_quantum_register(2, name='a')
    >>> b = builder.create_quantum_register(2, name='b')
    >>> builder.flip_if_equal(a, b, target=t)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -t[0]---------------X---------------------------------
                            |
    q1: -a[0]-X-X-----@-----|---------------------Z**b0-X-X---
              |       |     |                             |
    q2: -a[1]-|-X-X---|---@-@--------Z**b0--------------X-|-X-
              | |     |   | |        |                    | |
    q3: -b[0]-@-|-----|---|-|--------|--------------------@-|-
                |     |   | |        |                      |
    q4: -b[1]---@-----|---|-|--------|----------------------@-
                      |   | |        |
    q5:           |0>-X---@-|--------@-----HMR=b0
                          | |
    q6:               |0>-X-@-HMR=b0
```

## CircuitBuilder.flip_if_greater_than
```
flip_if_greater_than(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, or_equal: object = False, control: object = True, btol: float = inf) -> None


            @signature def flip_if_greater_than(self, lhs: km.array, rhs: km.array | int, *, target: km.q, or_equal: km.q | km.b | bool = False, control: km.q | km.b | bool = True, btol: float = float('inf')) -> None:
            Appends operations to perform `if control: target ^= lhs > rhs - or_equal`.

            Xors the result of an unsigned integer comparison into a target qubit.

            Args:
                lhs: The little-endian value on the left hand side of the comparison.
                rhs: The little-endian value or non-negative integer constant on the
                    right hand side of the comparison.
                target: The qubit to flip when lhs > rhs.
                or_equal: Defaults to False. Determines if the comparison is a
                    greater-than-or-equal-to test rather than a greater-than test.
                control: Defaults to True. Determines if the comparisons happens at all.
                btol: Defaults to infinity (exact). A finite value leads to a
                    cheaper circuit by only comparing the most significant bits,
                    since the rest only decide the answer when those tie. In
                    exchange, the answer can be wrong, but on no more than a
                    2**-btol fraction of inputs, assuming lhs and rhs are
                    independent and uniformly random. Holding one of them fixed
                    costs about a bit of that guarantee, and adversarial inputs
                    get no guarantee at all.

                    btol doesn't have to be an integer. Fractional values come up
                    naturally because approximation errors add up: doing k
                    approximate operations at btol + log2(k) each keeps the total
                    under 2**-btol.

                    A btol of len(lhs) or more is exact. A btol of 1 or less lets
                    the circuit skip the comparison entirely, since never
                    flipping the target is already right half the time.

            Examples:
                >>> import kickmix as km
                >>> builder = km.CircuitBuilder()
                >>> t = builder.create_quantum_register(1, name='t')[0]
                >>> a = builder.create_quantum_register(2, name='a')
                >>> builder.flip_if_greater_than(a, 1, target=t)
                >>> print(builder.finish_circuit().text_diagram())
                                            push_cond if b0     pop_cond
                q0: -t[0]---------X----------------------------------------X-
                                  |         neg
                q1: -a[0]-X-X-----|-------------------------Z-Z----------X-X-
                                  |
                q2: -a[1]-X-------@----------------------------------------X-
                                  |
                q3:         |0>-X-@-HMR=b0
                >>> # Greater-than-or-equal-to comparison:
                >>> builder = km.CircuitBuilder()
                >>> t = builder.create_quantum_register(1, name='t')[0]
                >>> a = builder.create_quantum_register(2, name='a')
                >>> builder.flip_if_greater_than(a, 1, target=t, or_equal=True)
                >>> print(builder.finish_circuit().text_diagram())
                                              push_cond if b0   pop_cond
                q0: -t[0]-----------X--------------------------------------X-
                                    |         neg
                q1: -a[0]-X-X---@---|-------------------------Z----------X-X-
                                |   |
                q2: -a[1]-X-----|---@--------------------------------------X-
                                |   |
                q3:         |0>-X-X-@-HMR=b0
                >>> # Controlled comparison:
                >>> builder = km.CircuitBuilder()
                >>> c = builder.create_quantum_register(1, name='c')[0]
                >>> t = builder.create_quantum_register(1, name='t')[0]
                >>> a = builder.create_quantum_register(2, name='a')
                >>> builder.flip_if_greater_than(a, 1, target=t, control=c)
                >>> print(builder.finish_circuit().text_diagram())
                                                       push_cond if b0     pop_cond
                q0: -c[0]-----------@----------@--------------------------------------@-
                                    |          |       neg                            |
                q1: -t[0]-----------|-X--------|--------------------------------------X-
                                    | |        |
                q2: -a[0]-X-X-------|-|--------|-----------------------Z-Z----------X-X-
                                    | |        |
                q3: -a[1]-X---------@-|--------Z**b0----------------------------------X-
                                    | |
                q4:         |0>-X---|-@--------HMR=b0
                                    | |
                q5:             |0>-X-@-HMR=b0
                >>> # Quantum-quantum comparison:
                >>> builder = km.CircuitBuilder()
                >>> t = builder.create_quantum_register(1, name='t')[0]
                >>> a = builder.create_quantum_register(2, name='a')
                >>> b = builder.create_quantum_register(2, name='b')
                >>> builder.flip_if_greater_than(a, b, target=t)
                >>> print(builder.finish_circuit().text_diagram())
                                                            push_cond if b0     pop_cond
                q0: -t[0]-------------------X---X--------------------------------------------X-
                                            |   |
                q1: -a[0]-X-X-------@-------|---|---------------------------Z-@----------X-X---
                            |       |       |   |                             |          |
                q2: -a[1]-X-|-X-----|-------|---@-----------------------------|----------|-X-X-
                            | |     |       |   |                             |          | |
                q3: -b[0]---@-|---X-@-X-@---|---|---------------------------Z-Z----------@-|---
                              |     |   |   |   |                                          |
                q4: -b[1]-----@-----|---|-@-@-@-|-@----------------------------------------@---
                                    |   | | | | | |
                q5:           |0>---X---X-X-X-X-@-X-HMR=b0
                >>> # Bounded tolerance comparison (comparing top bits only):
                >>> builder = km.CircuitBuilder()
                >>> t = builder.create_quantum_register(1, name='t')[0]
                >>> a = builder.create_quantum_register(4, name='a')
                >>> builder.flip_if_greater_than(a, 7, target=t, btol=2)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -t[0]---X-X-
                            |
                q1: -a[0]---|---
                            |
                q2: -a[1]---|---
                            |
                q3: -a[2]---|---
                            |
                q4: -a[3]-X-@-X-
```

## CircuitBuilder.flip_if_less_than
```
flip_if_less_than(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, or_equal: object = False, control: object = True, btol: float = inf) -> None

@signature def flip_if_less_than(self, lhs: km.array, rhs: km.array | int, *, target: km.q, or_equal: km.q | km.b | bool = False, control: km.q | km.b | bool = True, btol: float = float('inf')) -> None:
Appends operations to perform `if control: target ^= lhs < rhs + or_equal`.

Xors the result of an unsigned integer comparison into a target qubit.

Args:
    lhs: The little-endian value on the left hand side of the comparison.
    rhs: The little-endian value or non-negative integer constant on the
        right hand side of the comparison.
    target: The qubit to flip when lhs < rhs.
    or_equal: Defaults to False. Determines if the comparison is a
        less-than-or-equal-to test rather than a less-than test.
    control: Defaults to True. Determines if the comparisons happens at all.
    btol: Defaults to infinity (exact). A finite value leads to a
        cheaper circuit by only comparing the most significant bits,
        since the rest only decide the answer when those tie. In
        exchange, the answer can be wrong, but on no more than a
        2**-btol fraction of inputs, assuming lhs and rhs are
        independent and uniformly random. Holding one of them fixed
        costs about a bit of that guarantee, and adversarial inputs
        get no guarantee at all.

        btol doesn't have to be an integer. Fractional values come up
        naturally because approximation errors add up: doing k
        approximate operations at btol + log2(k) each keeps the total
        under 2**-btol.

        A btol of len(lhs) or more is exact. A btol of 1 or less lets
        the circuit skip the comparison entirely, since never
        flipping the target is already right half the time.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> target = builder.create_quantum_register(1, name="target")[0]
    >>> lhs = builder.create_quantum_register(1, name="lhs")
    >>> rhs = builder.create_quantum_register(1, name="rhs")
    >>> builder.flip_if_less_than(lhs, rhs, target=target)
    >>> builder.finish_circuit()
    km.Circuit('''
        APPEND_TO_REGISTER q0 r0
        REGISTER r0 "target"
        APPEND_TO_REGISTER q1 r1
        REGISTER r1 "lhs"
        APPEND_TO_REGISTER q2 r2
        REGISTER r2 "rhs"
        INFO_TAG "@enter:flip_if_lt"
        CX q2 q1
        CCX q1 q2 q0
        X q1
        X q1
        CX q2 q1
        INFO_TAG "@exit:flip_if_lt"
    ''')
```

## CircuitBuilder.free
```
free(self: kickmix.CircuitBuilder, arg: object) -> None

@signature def free(self, arg: km.q | km.b | km.array | Sequence[km.q | km.b]) -> None:
Frees allocated qubits or bits, so that they can be allocated again.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> q = builder.alloc_qubits(2)
    >>> builder.num_allocated_qubits
    2
    >>> builder.free(q)
    >>> builder.num_allocated_qubits
    0
```

## CircuitBuilder.gf2_iadd
```
gf2_iadd(self: kickmix.CircuitBuilder, offset: object, *, target: object, field: object = None, control: object = True) -> None

@signature def gf2_iadd(self, offset: km.array | int, *, target: km.array, field: km.GF2Field | None = None, control: km.q | km.b | bool = True) -> None:
Appends operations to perform `if control: target ^= offset` in GF(2^m).

Addition in a binary extension field is bitwise XOR, realized as a
layer of CNOTs (or Toffolis when quantum-controlled, or NOTs/CNOTs
when adding a classical constant).

Args:
    offset: The register or classical constant (int) to add. Left unchanged.
    target: The register to add into in place.
    field: Optional `km.GF2Field`. If provided, its degree must
        equal `len(target)`.
    control: Defaults to True. Determines if the addition occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> target = builder.create_quantum_register(2, name='target')
    >>> offset = builder.create_quantum_register(2, name='offset')
    >>> builder.gf2_iadd(offset, target=target)
    >>> builder.gf2_iadd(1, target=target)
    >>> builder.finish_circuit()
    km.Circuit('''
        APPEND_TO_REGISTER q0 r0
        APPEND_TO_REGISTER q1 r0
        REGISTER r0 "target"
        APPEND_TO_REGISTER q2 r1
        APPEND_TO_REGISTER q3 r1
        REGISTER r1 "offset"
        INFO_TAG "@enter:gf_iadd"
        CX q2 q0
        CX q3 q1
        INFO_TAG "@exit:gf_iadd"
        INFO_TAG "@enter:gf_iadd"
        X q0
        INFO_TAG "@exit:gf_iadd"
    ''')
```

## CircuitBuilder.gf2_idiv
```
gf2_idiv(self: kickmix.CircuitBuilder, divisor: object, *, target: object, field: object = None) -> None

@signature def gf2_idiv(self, divisor: int, *, target: km.array, field: km.GF2Field | None = None) -> None:
Appends operations to perform `target = (target / divisor) % modulus`.

Divides a GF(2^m) register in place by a non-zero classical divisor.
This is the exact inverse of `gf2_imul`.

Currently only classical integer divisors are supported; passing a
non-classical input raises `NotImplementedError`.

Args:
    divisor: The non-zero classical field element to divide by.
    target: The GF(2^m) register to divide in place.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> target = builder.create_quantum_register(2, name='target')
    >>> builder.gf2_idiv(2, target=target)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -target[0]-X-@-
                   | |
    q1: -target[1]-@-X-
```

## CircuitBuilder.gf2_imul
```
gf2_imul(self: kickmix.CircuitBuilder, factor: object, *, target: object, field: object = None) -> None

@signature def gf2_imul(self, factor: int, *, target: km.array, field: km.GF2Field | None = None) -> None:
Appends operations to perform `target = (target * factor) % modulus`.

Multiplies a GF(2^m) register in place by a non-zero classical factor
using only CNOT and SWAP gates (no ancillas or Toffolis).

Currently only classical integer factors are supported; passing a
non-classical input raises `NotImplementedError`.

Args:
    factor: The non-zero classical field element to multiply by.
    target: The GF(2^m) register to multiply in place.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> target = builder.create_quantum_register(2, name='target')
    >>> builder.gf2_imul(2, target=target)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -target[0]-X-SWAP-
                   | |
    q1: -target[1]-@-SWAP-
```

## CircuitBuilder.gf2_phase_by_product
```
gf2_phase_by_product(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, mask: object, field: object = None) -> None

@signature def gf2_phase_by_product(self, lhs: km.array, rhs: km.array, *, mask: km.array, field: km.GF2Field | None = None) -> None:
Negates amplitudes where `popcount(mask & (lhs * rhs) % modulus)` is odd.

Kicks back the phase of the product directly without computing it
into an intermediate register, using zero Toffolis and zero
ancillas.

Args:
    lhs: The first factor register. Left unchanged.
    rhs: The second factor register. Left unchanged.
    mask: Classical bits selecting which product bits contribute.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(lhs))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(2, name='lhs')
    >>> rhs = builder.create_quantum_register(2, name='rhs')
    >>> mask = builder.create_classical_register(2, name='mask')
    >>> builder.gf2_phase_by_product(lhs, rhs, mask=mask)
    >>> print(builder.finish_circuit().text_diagram())
                mask[0]=b0             b2^=1 if b0       b2^=1 if b0
    q0: -lhs[0]------------@-----------------------------------------
                mask[1]=b1 |           b2^=1 if b1       b2^=1 if b1
    q1: -lhs[1]------------|-----@-----------------@-----------------
                           |     |                 |
    q2: -rhs[0]------------Z**b0-Z**b1-------------|-----------------
                           |                       |
    q3: -rhs[1]------------Z**b1-------------------Z**b2-------------
```

## CircuitBuilder.hmr
```
hmr(self: kickmix.CircuitBuilder, target: object, output: object) -> None

@signature def hmr(self, target: km.q | km.array | Sequence[km.q], output: km.b | km.array | Sequence[km.b]) -> None:
Appends HMR (X-basis measurement and Z-basis reset) instructions.

Measures each target qubit in the X basis (storing the measurement
outcome into the corresponding `output` bit) and resets the qubit to
the |0> state. This method broadcasts over `km.array` and sequence
arguments of equal length.

Args:
    target: The qubit or array/sequence of qubits to measure in the
        X basis and reset to |0>.
    output: The classical bit or array/sequence of classical bits to
        store the measurement results into.

Raises:
    ValueError: `target` and `output` have different lengths, or
        contain non-qubit / non-bit items.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> q = builder.alloc_qubits(2)
    >>> b = builder.alloc_bits(2)
    >>> builder.hmr(q, b)
    >>> builder.finish_circuit()
    km.Circuit('''
        HMR q0 b0
        HMR q1 b1
    ''')
```

## CircuitBuilder.iadd
```
iadd(self: kickmix.CircuitBuilder, offset: object, *, target: object, control: object = True, btol: float = inf) -> None

@signature def iadd(self, offset: km.array | int, *, target: km.array, control: km.q | km.b | bool = True, btol: float = float('inf')) -> None:
Appends operations to perform `if control: target += offset`.

Performs an inplace 2s-complement addition modulo 2**len(target).
The offset can be a classical integer constant, classical bit
register, or a quantum register.

Args:
    offset: The little-endian value or integer to add. Can be
        classical or quantum.
    target: The little-endian quantum register to add into.
    control: Defaults to True. Determines if the addition occurs.
    btol: Defaults to infinity (exact). Only applies to a classical
        offset; passing a finite btol with a quantum offset is an
        error. A finite value can lead to a cheaper circuit by not
        carrying into the leading run of identical bits of offset,
        so there's nothing to save unless that run is longer than
        btol. In exchange, the sum can be wrong, but on no more than
        a 2**-btol fraction of target values, assuming target is
        uniformly random.

        btol doesn't have to be an integer. Fractional values come up
        naturally because approximation errors add up: doing k
        approximate operations at btol + log2(k) each keeps the total
        under 2**-btol.

        A btol of len(target) or more is exact.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> a = builder.create_quantum_register(2, name='a')
    >>> b = builder.create_quantum_register(2, name='b')
    >>> builder.iadd(b, target=a)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -a[0]-@-X---
              | |
    q1: -a[1]-X-|-X-
              | | |
    q2: -b[0]-@-@-|-
                  |
    q3: -b[1]-----@-
```

## CircuitBuilder.info_tag
```
info_tag(self: kickmix.CircuitBuilder, text: str) -> None

@signature def info_tag(self, text: str) -> None:
Appends an INFO_TAG instruction into the circuit.

INFO_TAG instructions have no effect on simulations, but can be used to make
debug information available. For example, the start of a  subroutine can be
hinted with `INFO_TAG "@enter:subroutine_name"` and its end can be indicated
with `INFO_TAG "@exit:subroutine_name"`.

Args:
    text: The content of the INFO_TAG instruction.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.info_tag("test")
    >>> builder.finish_circuit()
    km.Circuit('''
        INFO_TAG "test"
    ''')
```

## CircuitBuilder.init_and
```
init_and(self: kickmix.CircuitBuilder, control1: object, control2: object, target: object) -> None

@signature def init_and(self, control1: bool | km.b | km.q | km.array, control2: bool | km.b | km.q | km.array, target: km.q | km.array) -> None:
Initializes a qubit to `control1 and control2`, resetting it first.

This is the computation partner of `del_and`. It resets `target`
to |0> and then applies `CCX(control1, control2, target)`.

This method broadcasts over km.array arguments.

Args:
    control1: One of the controls of the AND.
    control2: The other control of the AND.
    target: The qubit initialized to the AND result.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> c1 = builder.alloc_qubits(1)[0]
    >>> c2 = builder.alloc_qubits(1)[0]
    >>> target = builder.alloc_qubits(1)[0]
    >>> builder.init_and(c1, c2, target)
    >>> builder.finish_circuit()
    km.Circuit('''
        R q2
        CCX q0 q1 q2
    ''')
```

## CircuitBuilder.init_gf2_div
```
init_gf2_div(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object = 'alloc', field: object = None) -> object

@signature def init_gf2_div(self, lhs: km.array, rhs: km.array, *, target: km.array | str = "alloc", field: km.GF2Field | None = None) -> km.array:
Initializes a GF(2^m) register to `(lhs / rhs) % modulus`, resetting it first.

This is the computation partner of `del_gf2_div`. Resets `target`
to |0> and then writes `lhs / rhs` into it. A zero divisor produces
a quotient of 0. The divisor's inverse and its addition chain are
temporary workspace, allocated and cleaned up automatically. Use
`init_gf2_div_with_scaffold` to keep them instead.

Args:
    lhs: The dividend register. Left unchanged.
    rhs: The divisor register. Left unchanged.
    target: The GF(2^m) register to initialize. Defaults to "alloc",
        which allocates a register of the field's degree.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(lhs))`.

Returns:
    The initialized register.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(8, name='lhs')
    >>> rhs = builder.create_quantum_register(8, name='rhs')
    >>> quotient = builder.init_gf2_div(lhs, rhs)
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like
    135
```

## CircuitBuilder.init_gf2_div_with_scaffold
```
init_gf2_div_with_scaffold(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object = 'alloc', field: object = None) -> object

@signature def init_gf2_div_with_scaffold(self, lhs: km.array, rhs: km.array, *, target: km.array | str = "alloc", field: km.GF2Field | None = None) -> tuple[km.array, km.array]:
Initializes `target := lhs / rhs`, keeping the division workspace.

Same as `init_gf2_div`, except the divisor's inverse and its
addition chain are kept rather than uncomputed. Keeping them lets
`del_gf2_div_with_scaffold` undo the whole thing with zero
Toffolis, which is cheaper than recomputing the inverse.

This is the computation partner of `del_gf2_div_with_scaffold`.

Args:
    lhs: The dividend register. Left unchanged.
    rhs: The divisor register. Left unchanged.
    target: The GF(2^m) register to initialize. Defaults to "alloc",
        which allocates a register of the field's degree.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(lhs))`.

Returns:
    A tuple of the initialized register and the scaffold register
    holding the divisor's inverse and addition chain.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(8, name='lhs')
    >>> rhs = builder.create_quantum_register(8, name='rhs')
    >>> quotient, scaffold = builder.init_gf2_div_with_scaffold(lhs, rhs)
    >>> len(scaffold)
    32
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like
    135
```

## CircuitBuilder.init_gf2_inverse
```
init_gf2_inverse(self: kickmix.CircuitBuilder, input: object, *, target: object = 'alloc', field: object = None) -> object

@signature def init_gf2_inverse(self, input: km.array, *, target: km.array | str = "alloc", field: km.GF2Field | None = None) -> km.array:
Initializes `target := input ** -1` in GF(2^m) (mapping 0 to 0).

This is the computation partner of `del_gf2_inverse`. Resets
`target` to |0> and then writes the inverse into it, using the
Itoh-Tsujii addition chain. The chain's intermediates are temporary
workspace, allocated and cleaned up automatically. Use
`init_gf2_inverse_with_scaffold` to keep them instead, which makes
the matching uncomputation free of Toffolis.

Args:
    input: The GF(2^m) register to invert. Left unchanged.
    target: The register to store the inverse into. Defaults to
        "alloc", which allocates a register of the field's degree.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(input))`.

Returns:
    The initialized register.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> inp = builder.create_quantum_register(2, name='inp')
    >>> inv = builder.init_gf2_inverse(inp)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -inp[0]-@-----
                |
    q1: -inp[1]-|-@---
                | |
    q2:  |0>----X-|-X-
                  | |
    q3:  |0>------X-@-
```

## CircuitBuilder.init_gf2_inverse_with_scaffold
```
init_gf2_inverse_with_scaffold(self: kickmix.CircuitBuilder, input: object, *, target: object = 'alloc', field: object = None) -> object

@signature def init_gf2_inverse_with_scaffold(self, input: km.array, *, target: km.array | str = "alloc", field: km.GF2Field | None = None) -> tuple[km.array, km.array]:
Initializes `target := input ** -1`, keeping the addition chain.

Same as `init_gf2_inverse`, except the Itoh-Tsujii addition chain
intermediates are kept rather than uncomputed. Keeping them lets
`del_gf2_inverse_with_scaffold` undo the whole thing with zero
Toffolis, which is cheaper than recomputing the chain.

This is the computation partner of `del_gf2_inverse_with_scaffold`.

Args:
    input: The GF(2^m) register to invert. Left unchanged.
    target: The register to store the inverse into. Defaults to
        "alloc", which allocates a register of the field's degree.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(input))`.

Returns:
    A tuple of the initialized register and the scaffold register
    holding the addition chain.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> inp = builder.create_quantum_register(8, name='inp')
    >>> inv, scaffold = builder.init_gf2_inverse_with_scaffold(inp)
    >>> len(scaffold)
    24
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like
    108
```

## CircuitBuilder.init_gf2_mul
```
init_gf2_mul(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object = 'alloc', field: object = None, control: object = True) -> object

@signature def init_gf2_mul(self, lhs: km.array, rhs: km.array, *, target: km.array | str = "alloc", field: km.GF2Field | None = None, control: km.q | km.b | bool = True) -> km.array:
Initializes a GF(2^m) register to `(lhs * rhs) % modulus`, resetting it first.

This is the computation partner of `del_gf2_mul`. Resets `target`
to |0> and then multiplies `lhs` and `rhs` into `target`.

Args:
    lhs: The first factor register. Left unchanged.
    rhs: The second factor register. Left unchanged.
    target: The GF(2^m) register to initialize. Defaults to "alloc",
        which allocates a register of the field's degree.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(lhs))`.
    control: Defaults to True. Determines if the operation occurs.

Returns:
    The initialized register.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(2, name='lhs')
    >>> rhs = builder.create_quantum_register(2, name='rhs')
    >>> target = builder.init_gf2_mul(lhs, rhs)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -lhs[0]---X----@-X---------------@-----
                  |    | |               |
    q1: -lhs[1]---@----|-@------@--------|-----
                       |        |        |
    q2: -rhs[0]---X----@-X------|--------@-----
                  |    | |      |        |
    q3: -rhs[1]---@----|-@------@--------|-----
                       |        |        |
    q4:  |0>----@-SWAP-X-X-SWAP-X-X-SWAP-X-X-@-
                | |      | |      | |      | |
    q5:  |0>----X-SWAP---@-SWAP---@-SWAP---@-X-
```

## CircuitBuilder.init_lookup
```
init_lookup(self: kickmix.CircuitBuilder, *, table: object, address: object, target: object) -> None

@signature def init_lookup(self, *, table: Iterable[int], address: km.array, target: km.array) -> None:
Appends operations to perform `let target := table[address]`.

Looks up a value from a classical table, indexed by a quantum register.

Because this is an `init` method, the target qubits must start in the 0
state. The target qubits will be reset before being used, transforming
any bit errors into probabilistic phase errors.

Args:
    table: The table of classical values, as a list of python integers.
        The integers are interpreted in a little-endian fashion, meaning
        that `table_data[address, out_index] ==
        (table[address] >> out_index) & 1`.
    address: The address used to select a value from the table.
    target: The clean qubits to store the output into.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(2, name='address')
    >>> target = builder.create_quantum_register(4, name='target')
    >>> builder.init_lookup(
    ...     table=[2, 3, 5, 7],
    ...     address=address,
    ...     target=target,
    ... )
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.use_same_registers_as(circuit)
    >>> for a in range(4):
    ...     sim.write_within_shot('address', a, a)
    >>> sim.do(circuit)
    >>> [sim.read_within_shot('target', a, out=int) for a in range(4)]
    [2, 3, 5, 7]
```

## CircuitBuilder.isub
```
isub(self: kickmix.CircuitBuilder, offset: object, *, target: object, control: object = True, btol: float = inf) -> None

@signature def isub(self, offset: km.array | int, *, target: km.array, control: km.q | km.b | bool = True, btol: float = float('inf')) -> None:
Appends operations to perform `if control: target -= offset`.

Performs an inplace 2s-complement subtraction modulo 2**len(target).
The offset can be a classical integer constant, classical bit
register, or a quantum register.

Args:
    offset: The little-endian value or integer to subtract. Can be
        classical or quantum.
    target: The little-endian quantum register to subtract from.
    control: Defaults to True. Determines if the subtraction occurs.
    btol: Defaults to infinity (exact). Only applies to a classical
        offset; passing a finite btol with a quantum offset is an
        error. A finite value can lead to a cheaper circuit by not
        borrowing into the leading run of identical bits of offset,
        so there's nothing to save unless that run is longer than
        btol. In exchange, the difference can be wrong, but on no
        more than a 2**-btol fraction of target values, assuming
        target is uniformly random.

        btol doesn't have to be an integer. Fractional values come up
        naturally because approximation errors add up: doing k
        approximate operations at btol + log2(k) each keeps the total
        under 2**-btol.

        A btol of len(target) or more is exact.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> a = builder.create_quantum_register(2, name='a')
    >>> b = builder.create_quantum_register(2, name='b')
    >>> builder.isub(b, target=a)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -a[0]-X-@-X-X---
                | |
    q1: -a[1]-X-X-|-X-X-
                | | |
    q2: -b[0]---@-@-|---
                    |
    q3: -b[1]-------@---
```

## CircuitBuilder.ixor_gf2_div
```
ixor_gf2_div(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, field: object = None) -> None

@signature def ixor_gf2_div(self, lhs: km.array, rhs: km.array, *, target: km.array, field: km.GF2Field | None = None) -> None:
Appends operations to perform `target ^= (lhs / rhs) % modulus`.

Out-of-place division accumulating the quotient into `target` via
bitwise XOR. Does not reset `target` or assume it is in the |0>
state. A zero divisor produces a quotient of 0. Temporary workspace
is allocated and cleaned up automatically.

Args:
    lhs: The dividend register. Left unchanged.
    rhs: The divisor register. Left unchanged.
    target: The GF(2^m) register to XOR the quotient into.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> lhs = builder.create_quantum_register(8, name='lhs')
    >>> rhs = builder.create_quantum_register(8, name='rhs')
    >>> target = builder.create_quantum_register(8, name='target')
    >>> builder.ixor_gf2_div(lhs, rhs, target=target)
    >>> circuit = builder.finish_circuit()
    >>> stats = circuit.operation_statistics()
    >>> stats.num_toffoli_like
    135
```

## CircuitBuilder.ixor_gf2_mul
```
ixor_gf2_mul(self: kickmix.CircuitBuilder, lhs: object, rhs: object, *, target: object, field: object = None, control: object = True) -> None

@signature def ixor_gf2_mul(self, lhs: km.array, rhs: km.array, *, target: km.array, field: km.GF2Field | None = None, control: km.q | km.b | bool = True) -> None:
Appends operations to perform `if control: target ^= (lhs * rhs) % modulus`.

Out-of-place multiplication accumulating the product into `target`
via bitwise XOR. Does not reset `target` or assume it is in the
|0> state.

Args:
    lhs: The first factor register. Left unchanged.
    rhs: The second factor register. Left unchanged.
    target: The GF(2^m) register to XOR the product into.
    field: Optional `km.GF2Field`. Defaults to
        `km.GF2Field(len(target))`.
    control: Defaults to True. Determines if the operation occurs.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> target = builder.create_quantum_register(2, name='target')
    >>> lhs = builder.create_quantum_register(2, name='lhs')
    >>> rhs = builder.create_quantum_register(2, name='rhs')
    >>> builder.ixor_gf2_mul(lhs, rhs, target=target)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -target[0]-@-SWAP-X-X-SWAP-X-X-SWAP-X-X-@-
                   | |    | | |    | | |    | | |
    q1: -target[1]-X-SWAP-|-@-SWAP-|-@-SWAP-|-@-X-
                          |        |        |
    q2: -lhs[0]------X----@-X------|--------@-----
                     |    | |      |        |
    q3: -lhs[1]------@----|-@------@--------|-----
                          |        |        |
    q4: -rhs[0]------X----@-X------|--------@-----
                     |      |      |
    q5: -rhs[1]------@------@------@--------------
```

## CircuitBuilder.left_rotate
```
left_rotate(self: kickmix.CircuitBuilder, target: object, shift: object = 1, *, control: object = True) -> None


            @signature def left_rotate(self, target: km.array | Sequence[km.q], shift: int | km.array | Sequence[km.q | km.b | bool] = 1, *, control: km.q | km.b | bool = True) -> None:
            Left rotates the given qubits, cyclically permuting them.

            A left rotation is a permutation that moves the value of the qubit target[k]
            into the qubit target[(k + shift) % len(target)].

            Args:
                target: The qubits to permute.
                shift: Defaults to 1. A little-endian value specifying how much to
                    left-rotate the target qubits.
                control: Defaults to True. Determines if the left rotation actually occurs.

            Examples:
                >>> import kickmix as km

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(8, name='target')
                >>> builder.left_rotate(target)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP-------------------------------
                               |
                q1: -target[1]-|----SWAP-----------SWAP-----------
                               |    |              |
                q2: -target[2]-|----|----SWAP------|----SWAP------
                               |    |    |         |    |
                q3: -target[3]-|----|----|----SWAP-|----|----SWAP-
                               |    |    |    |    |    |    |
                q4: -target[4]-|----|----|----SWAP-|----|----|----
                               |    |    |         |    |    |
                q5: -target[5]-|----|----SWAP------|----|----SWAP-
                               |    |              |    |
                q6: -target[6]-|----SWAP-----------|----SWAP------
                               |                   |
                q7: -target[7]-SWAP----------------SWAP-----------

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(8, name='target')
                >>> builder.left_rotate(target, 3)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP-----------SWAP-----------
                               |              |
                q1: -target[1]-|----SWAP------|--------------
                               |    |         |
                q2: -target[2]-|----|----SWAP-SWAP-----------
                               |    |    |
                q3: -target[3]-|----|----|----SWAP-SWAP------
                               |    |    |    |    |
                q4: -target[4]-|----|----|----SWAP-|----SWAP-
                               |    |    |         |    |
                q5: -target[5]-|----|----SWAP------|----|----
                               |    |              |    |
                q6: -target[6]-|----SWAP-----------|----SWAP-
                               |                   |
                q7: -target[7]-SWAP----------------SWAP------

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(4, name='target')
                >>> control = builder.create_quantum_register(1, name='control')[0]
                >>> builder.left_rotate(target, 2, control=control)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]--SWAP------SWAP------
                                |         |
                q1: -target[1]--|----SWAP-SWAP------
                                |    |    |
                q2: -target[2]--|----SWAP-|----SWAP-
                                |    |    |    |
                q3: -target[3]--SWAP-|----|----SWAP-
                                |    |    |    |
                q4: -control[0]-@----@----@----@----

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(6, name='target')
                >>> shift = builder.create_quantum_register(3, name='shift')
                >>> builder.left_rotate(target, shift)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP-------------SWAP----------SWAP--------SWAP------
                               |                |             |           |
                q1: -target[1]-SWAP-------------|-------------|----SWAP---|---------
                               |                |             |    |      |
                q2: -target[2]-|----SWAP--------SWAP----------|----|------SWAP------
                               |    |           |             |    |      |
                q3: -target[3]-|----|----SWAP---|----SWAP-----|----SWAP---|----SWAP-
                               |    |    |      |    |        |    |      |    |
                q4: -target[4]-|----|----SWAP---|----|--------SWAP-|------|----|----
                               |    |    |      |    |        |    |      |    |
                q5: -target[5]-|----SWAP-|------|----SWAP-----|----|------|----SWAP-
                               |    |    |      |    |        |    |      |    |
                q6: -shift[0]--@----@----@----@-|----|----@---|----|------|----|----
                                              | |    |    |   |    |      |    |
                q7: -shift[1]-----------------X-@----@----X-@-|----|----@-|----|----
                                                            | |    |    | |    |
                q8: -shift[2]-------------------------------X-@----@----X-@----@----
```

## CircuitBuilder.mark
```
mark(self: kickmix.CircuitBuilder, name: str) -> kickmix._CircuitBuilderMark

@signature def mark(self, name: str) -> Any:
Returns a context manager that emits @enter/@exit INFO_TAG instructions.

These INFO_TAG instructions are intended as debug information about entering
and exiting subroutines. For example, they are used by
`km.Circuit.flame_chart_svg()`.

Args:
    name: Label shown for the block in `builder.flame_chart_svg()`.

Returns:
    A context manager that marks blocks under `name`.

Examples:
    >>> import pathlib
    >>> import tempfile
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(4, name='address')
    >>> total = builder.create_quantum_register(8, name='total')
    >>> lookup_mark = builder.mark('iadd_lookup')
    >>> def iadd_lookup(table: list[int], idx: km.array, dst: km.array):
    ...     with lookup_mark:
    ...         buf = builder.alloc_qubits(len(dst))
    ...         builder.init_lookup(table=table, address=idx, target=buf)
    ...         builder.iadd(buf, target=dst)
    ...         builder.del_lookup(table=table, address=idx, target=buf)
    ...         builder.free(buf)
    >>> with builder.mark('accumulate_tables'):
    ...     iadd_lookup([3 * k for k in range(16)], address, total)
    ...     iadd_lookup([k * k for k in range(16)], address, total)
    >>> circuit = builder.finish_circuit()
    >>> with tempfile.TemporaryDirectory() as d:
    ...     with open(pathlib.Path(d) / 'flame_chart.svg', 'w') as f:
    ...         print(circuit.flame_chart_svg(), file=f)
```

## CircuitBuilder.max_qubits
```
@signature def max_qubits(self) -> int | float:
Returns the maximum number of qubits allowed when building circuits.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.max_qubits
    inf
    >>> builder.set_max_qubits(500)
    >>> builder.max_qubits
    500
```

## CircuitBuilder.multi_controlled_x
```
multi_controlled_x(self: kickmix.CircuitBuilder, controls: object, target: object) -> None

@signature def multi_controlled_x(self, controls: km.array | Sequence[km.q | km.b | bool], target: km.q | km.array | Sequence[km.q]) -> None:
Appends a multi-controlled NOT operation to the circuit.

Flips every qubit in `target` when all `controls` are satisfied.
When there are 3 or more quantum controls, temporary workspace
qubits are allocated from the builder to compute the AND ladder and
uncomputed using measurement-based uncomputation (`del_and`).

Args:
    controls: A sequence or `km.array` of quantum controls (`km.q`),
        classical bit controls (`km.b`), or boolean constants
        (`bool`) that must all be satisfied for the target qubits to
        flip.
    target: The qubit or array/sequence of qubits to flip when all
        controls are satisfied.

Raises:
    TypeError: `controls` is not a sequence or `km.array`.
    ValueError: `controls` or `target` contains invalid item types.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> c = builder.alloc_qubits(3)
    >>> t = builder.alloc_qubits(1)[0]
    >>> builder.multi_controlled_x(c, t)
    >>> builder.finish_circuit()
    km.Circuit('''
        R q4
        CCX q0 q1 q4
        CCX q2 q4 q3
        HMR q4 b0
        CZ q1 q0 if b0
    ''')
```

## CircuitBuilder.neg
```
neg(self: kickmix.CircuitBuilder) -> None

Appends a NEG instruction that flips the global phase by -1.

Inside a classical condition block (see `push_condition`), or when
tracking shot phases in `km.Simulator`, `NEG` negates the amplitude
of the current branch.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.neg()
    >>> builder.finish_circuit()
    km.Circuit('''
        NEG
    ''')
```

## CircuitBuilder.neg_if
```
neg_if(self: kickmix.CircuitBuilder, condition: object) -> None

@signature def neg_if(self, condition: km.b) -> None:
Appends a classically-conditioned NEG instruction to the circuit.

Flips the global phase by -1 in shots where the given classical bit
is True.

Args:
    condition: The classical bit (`km.b`) that controls whether the
        phase flip occurs.

Raises:
    TypeError: `condition` is not a `km.b`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.neg_if(km.b(0))
    >>> builder.finish_circuit()
    km.Circuit('''
        NEG if b0
    ''')
```

## CircuitBuilder.num_allocated_qubits
```
Returns the current number of allocated qubits.
```

## CircuitBuilder.num_free_qubits
```
@signature def num_free_qubits(self) -> int | float:
Returns how many more qubits can be allocated before hitting max_qubits.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> _ = builder.alloc_qubits(4)
    >>> builder.num_free_qubits
    inf
    >>> builder.set_max_qubits(500)
    >>> builder.num_free_qubits
    496
    >>> _ = builder.alloc_qubits(4)
    >>> builder.num_free_qubits
    492
```

## CircuitBuilder.pop_condition
```
pop_condition(self: kickmix.CircuitBuilder) -> None

Appends a POP_CONDITION instruction to pop from the condition stack.

Should be paired with a preceding call to `push_condition`. A POP_CONDITION
without a prior PUSH_CONDITION has no effect on simulation state.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.push_condition(km.b(0))
    >>> builder.x(km.q(0))
    >>> builder.pop_condition()
    >>> builder.finish_circuit()
    km.Circuit('''
        PUSH_CONDITION if b0
        X q0
        POP_CONDITION
    ''')
```

## CircuitBuilder.push_condition
```
push_condition(self: kickmix.CircuitBuilder, condition: object) -> None

@signature def push_condition(self, condition: km.b) -> None:
Appends a PUSH_CONDITION instruction to push a bit onto the condition stack.

All subsequent instructions in the circuit will only execute in
shots where all bits currently on the condition stack are True,
until a matching `pop_condition` is called.

Args:
    condition: The classical bit (`km.b`) to push onto the condition
        stack.

Raises:
    TypeError: `condition` is not a `km.b`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.push_condition(km.b(0))
    >>> builder.x(km.q(0))
    >>> builder.pop_condition()
    >>> builder.finish_circuit()
    km.Circuit('''
        PUSH_CONDITION if b0
        X q0
        POP_CONDITION
    ''')
```

## CircuitBuilder.reset
```
reset(self: kickmix.CircuitBuilder, target: object) -> None

@signature def reset(self, target: km.q | km.array | Sequence[km.q]) -> None:
Appends Z-basis reset (R) instructions to the circuit.

Resets each target qubit to the |0> state. This method broadcasts
over `km.array` and sequence arguments.

Args:
    target: The qubit or array/sequence of qubits to reset.

Raises:
    ValueError: `target` contains non-qubit items.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> q = builder.alloc_qubits(2)
    >>> builder.reset(q)
    >>> builder.finish_circuit()
    km.Circuit('''
        R q0
        R q1
    ''')
```

## CircuitBuilder.right_rotate
```
right_rotate(self: kickmix.CircuitBuilder, target: object, shift: object = 1, *, control: object = True) -> None


            @signature def right_rotate(self, target: km.array | Sequence[km.q], shift: int | km.array | Sequence[km.q | km.b | bool] = 1, *, control: km.q | km.b | bool = True) -> None:
            Right rotates the given qubits, cyclically permuting them.

            A right rotation is a permutation that moves the value of the qubit target[k]
            into the qubit target[(k - shift) % len(target)].

            Args:
                target: The qubits to permute.
                shift: Defaults to 1. A little-endian value specifying how much to
                    right-rotate the target qubits.
                control: Defaults to True. Determines if the right rotation actually occurs.

            Examples:
                >>> import kickmix as km

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(8, name='target')
                >>> builder.right_rotate(target)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP----------------SWAP-----------
                               |                   |
                q1: -target[1]-|----SWAP-----------|----SWAP------
                               |    |              |    |
                q2: -target[2]-|----|----SWAP------|----|----SWAP-
                               |    |    |         |    |    |
                q3: -target[3]-|----|----|----SWAP-|----|----|----
                               |    |    |    |    |    |    |
                q4: -target[4]-|----|----|----SWAP-|----|----SWAP-
                               |    |    |         |    |
                q5: -target[5]-|----|----SWAP------|----SWAP------
                               |    |              |
                q6: -target[6]-|----SWAP-----------SWAP-----------
                               |
                q7: -target[7]-SWAP-------------------------------

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(8, name='target')
                >>> builder.right_rotate(target, 3)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP----------------SWAP------
                               |                   |
                q1: -target[1]-|----SWAP-----------|----SWAP-
                               |    |              |    |
                q2: -target[2]-|----|----SWAP------|----|----
                               |    |    |         |    |
                q3: -target[3]-|----|----|----SWAP-|----SWAP-
                               |    |    |    |    |
                q4: -target[4]-|----|----|----SWAP-SWAP------
                               |    |    |
                q5: -target[5]-|----|----SWAP-----------SWAP-
                               |    |                   |
                q6: -target[6]-|----SWAP----------------|----
                               |                        |
                q7: -target[7]-SWAP---------------------SWAP-

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(4, name='target')
                >>> control = builder.create_quantum_register(1, name='control')[0]
                >>> builder.right_rotate(target, 2, control=control)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]--SWAP------SWAP------
                                |         |
                q1: -target[1]--|----SWAP-SWAP------
                                |    |    |
                q2: -target[2]--|----SWAP-|----SWAP-
                                |    |    |    |
                q3: -target[3]--SWAP-|----|----SWAP-
                                |    |    |    |
                q4: -control[0]-@----@----@----@----

                >>> builder = km.CircuitBuilder()
                >>> target = builder.create_quantum_register(6, name='target')
                >>> shift = builder.create_quantum_register(3, name='shift')
                >>> builder.right_rotate(target, shift)
                >>> print(builder.finish_circuit().text_diagram())
                q0: -target[0]-SWAP-------------SWAP----------SWAP--------SWAP------
                               |                |             |           |
                q1: -target[1]-|----SWAP--------|----SWAP-----|-----------|----SWAP-
                               |    |           |    |        |           |    |
                q2: -target[2]-|----|----SWAP---|----|--------SWAP--------|----|----
                               |    |    |      |    |        |           |    |
                q3: -target[3]-|----|----SWAP---|----SWAP-----|----SWAP---|----SWAP-
                               |    |    |      |    |        |    |      |    |
                q4: -target[4]-|----SWAP-|------SWAP-|--------|----|------SWAP-|----
                               |    |    |      |    |        |    |      |    |
                q5: -target[5]-SWAP-|----|------|----|--------|----SWAP---|----|----
                               |    |    |      |    |        |    |      |    |
                q6: -shift[0]--@----@----@----@-|----|----@---|----|------|----|----
                                              | |    |    |   |    |      |    |
                q7: -shift[1]-----------------X-@----@----X-@-|----|----@-|----|----
                                                            | |    |    | |    |
                q8: -shift[2]-------------------------------X-@----@----X-@----@----
```

## CircuitBuilder.set_max_qubits
```
set_max_qubits(self: kickmix.CircuitBuilder, limit: object) -> None

@signature def set_max_qubits(self, limit: int | float) -> None:

Sets the maximum number of qubits allowed when building circuits.

Attempting to allocate more qubits than the maximum will cause the allocation
to raise an exception. This includes both qubits returned by
`CircuitBuilder.alloc_qubits` and by `CircuitBuilder.create_quantum_register`.

Args:
    limit: The maximum number of qubits that can be allocated.
        Set to `float('inf')` to disable the limit.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.set_max_qubits(4)
    >>> builder.max_qubits
    4
    >>> q = builder.alloc_qubits(3)
    >>> builder.num_free_qubits
    1
```

## CircuitBuilder.swap
```
swap(self: kickmix.CircuitBuilder, target1: object, target2: object) -> None

@signature def swap(self, target1: km.q | km.b | km.xb | km.array, target2: km.q | km.b | km.xb | km.array) -> None:
Appends SWAP gates to the circuit.

Swaps the values of `target1` and `target2`. This method broadcasts
over `km.array` and sequence arguments.

Swapping qubits emits `SWAP` instructions. Swapping classical bits
(`km.b` or `km.xb`) emits three `BIT_INVERT ... if ...` instructions.

Args:
    target1: The first qubit, bit, or register to swap.
    target2: The second qubit, bit, or register to swap.

Raises:
    ValueError: Broadcast array lengths do not match, or `target1`
        and `target2` do not have matching swappable types.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> x = builder.create_quantum_register(2, name='x')
    >>> y = builder.create_quantum_register(2, name='y')
    >>> builder.swap(x, y)
    >>> print(builder.finish_circuit().text_diagram())
    q0: -x[0]-SWAP------
              |
    q1: -x[1]-|----SWAP-
              |    |
    q2: -y[0]-SWAP-|----
                   |
    q3: -y[1]------SWAP-
```

## CircuitBuilder.unary_iteration
```
unary_iteration(self: kickmix.CircuitBuilder, address: object, address_values: object = None, *, control: object = True) -> kickmix.UnaryIterationCursor

@signature def unary_iteration(self, address: km.array, address_values: range | None = None, *, control: km.q | km.b | bool = True) -> km.UnaryIterationCursor:
Returns a cursor for stepping through values of `address`.

Use `with builder.unary_iteration(...) as it:` to open a pass. Inside the
`with` block, loop over `it` to visit `(address_value, match_qubit)` pairs
in order, or call `it.move_to(v)` to jump to any value `v`. At each step,
`it.match_qubit` is a qubit that is ON in the parts of the superposition
where `control` is active and `address == v`.

Opening the `with` block allocates `max(1, len(address))` temporary qubits,
and exiting the block uncomputes and frees them. Do not modify `address`,
`control`, or `match_qubit` while the pass is open, and only use
`match_qubit` as a control.

For a non-empty `address`, positioning at the first in-range value currently
costs at most `len(address)` Toffoli gates when `control` is a qubit, or
`len(address) - 1` when `control` is `True` or a classical bit. Moving
between distinct in-range values `a` and `b` costs at most
`(a ^ b).bit_length() - 1` Toffoli gates, and closing the pass costs zero
Toffoli gates.

Args:
    address: The little-endian address to match against (at most 63 qubits).
    address_values: Defaults to `range(1 << len(address))`. The step-1 `range`
        of values visited by `for` loops.
    control: Gates the iteration when provided. If `False`, no operations are
        emitted and `for` loops visit zero values. Defaults to `True`.

Returns:
    A reusable cursor over `address` that can be opened with `with`.

Examples:
    >>> import kickmix as km
    >>> # Sequential iteration over a range of address values:
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(3, name='address')
    >>> target = builder.create_quantum_register(1, name='target')
    >>> with builder.unary_iteration(address, range(4)) as it:
    ...     for address_value, match_qubit in it:
    ...         if address_value == 1:
    ...             builder.cx(match_qubit, target[0])
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=8)
    >>> sim.use_same_registers_as(circuit)
    >>> for a in range(8):
    ...     sim.write_within_shot('address', a, a)
    >>> sim.do(circuit)
    >>> for a in range(8):
    ...     print(f"{a}: {sim.read_within_shot('target', a, out=int)}")
    0: 0
    1: 1
    2: 0
    3: 0
    4: 0
    5: 0
    6: 0
    7: 0

    >>> # Random-access jumps using move_to:
    >>> builder = km.CircuitBuilder()
    >>> address = builder.create_quantum_register(3, name='address')
    >>> target = builder.create_quantum_register(1, name='target')
    >>> with builder.unary_iteration(address) as it:
    ...     for address_value in [5, 2, 7]:
    ...         it.move_to(address_value)
    ...         builder.cx(it.match_qubit, target[0])
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=8)
    >>> sim.use_same_registers_as(circuit)
    >>> for a in range(8):
    ...     sim.write_within_shot('address', a, a)
    >>> sim.do(circuit)
    >>> for a in range(8):
    ...     print(f"{a}: {sim.read_within_shot('target', a, out=int)}")
    0: 0
    1: 0
    2: 1
    3: 0
    4: 0
    5: 1
    6: 0
    7: 1
```

## CircuitBuilder.x
```
x(self: kickmix.CircuitBuilder, target: object) -> None

@signature def x(self, target: km.q | km.b | km.xb | km.xbool | Literal['|+>', '|->'] | km.array | Sequence[km.q | km.b | km.xb | km.xbool]) -> None:
Appends NOT gates (or their classical/phase equivalents) to the circuit.

This method broadcasts over `km.array` and sequence arguments.
Depending on the type of `target`, it emits `X` for qubits (`km.q`),
`BIT_INVERT` for classical bits (`km.b`), `NEG_IF` for X-basis bits
(`km.xb`), and `NEG` for `km.xbool(True)` or `'|->'`.

Args:
    target: The qubit, bit, X-basis bit, X-basis bool, or
        array/sequence of them to flip.

Raises:
    ValueError: Attempted to invert a compile-time `bool`.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.x(km.q(0))
    >>> builder.x(km.b(1))
    >>> builder.x(km.xb(2))
    >>> builder.x('|->')
    >>> builder.finish_circuit()
    km.Circuit('''
        X q0
        BIT_INVERT b1
        NEG if b2
        NEG
    ''')
```

## CircuitBuilder.z
```
z(self: kickmix.CircuitBuilder, target: object) -> None

@signature def z(self, target: km.q | km.b | bool | km.array | Sequence[km.q | km.b | bool]) -> None:
Appends Z gates (or their classical/constant equivalents) to the circuit.

This method broadcasts over `km.array` and sequence arguments.
Depending on the type of `target`, this emits `Z` for a qubit
(`km.q`), `NEG_IF` for a classical bit (`km.b`), `NEG` for `True`,
and nothing for `False`.

Args:
    target: The qubit, classical bit, boolean, or array/sequence of
        them determining if phasing occurs.

Raises:
    TypeError: `target` is not a `km.q`, `km.b`, `bool`, or
        array/sequence of them.
    ValueError: `target` contains X-basis values (`km.xb` or
        `km.xbool`).

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> builder.z(km.q(0))
    >>> builder.z(km.b(1))
    >>> builder.z(True)
    >>> builder.z(False)
    >>> builder.finish_circuit()
    km.Circuit('''
        Z q0
        NEG if b1
        NEG
    ''')
```

## CircuitBuilder.z_pow
```
z_pow(self: kickmix.CircuitBuilder, target: object, exponent: object) -> None


            @signature def z_pow(self, target: km.q | km.array | Sequence[km.q], exponent: float | int | fractions.Fraction | str) -> None:
            Appends Z_POW gates to the circuit.

            This method broadcasts over km.array arguments. If the target is a sequence
            of qubits, rather than a single qubit, an operation is appended for each qubit.

            Args:
                target: The qubit(s) to apply Z_POW to.
                exponent: The exponent of the Z_POW operation.
                    The exponent is converted into a fractions.Fraction, then canonicalized
                    into the range [0, 2) and rounded to the nearest multiple of 2**-127.

            Examples:
                >>> import kickmix as km

                >>> # Demo a simple z_pow call
                >>> builder = km.CircuitBuilder()
                >>> builder.z_pow(km.q(0), 0.25)
                >>> builder.finish_circuit()
                km.Circuit('''
                    Z_POW q0 0.25
                ''')

                >>> # Demo a broadcasting call
                >>> builder = km.CircuitBuilder()
                >>> targets = builder.create_quantum_register(3, "targets")
                >>> builder.z_pow(targets, -0.5)
                >>> builder.finish_circuit()
                km.Circuit('''
                    APPEND_TO_REGISTER q0 r0
                    APPEND_TO_REGISTER q1 r0
                    APPEND_TO_REGISTER q2 r0
                    REGISTER r0 "targets"
                    Z_POW q0 1.5
                    Z_POW q1 1.5
                    Z_POW q2 1.5
                ''')
```

## Simulator.batch_size
```
The number of shots being tracked by the simulator.
```

## Simulator.clear_for_shot
```
clear_for_shot(self: kickmix.Simulator) -> None

Zeroes all data that should be reset between shots from a circuit.

When using the simulator to repeatedly sample from a circuit, it is important
to call clear_for_shot between calls. Otherwise state modified by an earlier
shot may end up affecting a later shot.

This method clears:
- tracked qubit values
- tracked bit values
- tracked phase values
- the condition stack

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=8)
    >>> sim.do(km.Circuit('''
    ...     X q0
    ...     PUSH_CONDITION if b0
    ... '''))
    >>> sim.read_across_shots(km.q(0), out=int)
    255

    >>> sim.clear_for_shot()
    >>> sim.read_across_shots(km.q(0), out=int)
    0
```

## Simulator.clear_operation_statistics
```
clear_operation_statistics(self: kickmix.Simulator) -> None

Zeroes all accumulated operation statistics on the simulator.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=4, counting_operations=True)
    >>> sim.do(km.Circuit('X q0'))
    >>> sim.operation_statistics()['X']
    4
    >>> sim.clear_operation_statistics()
    >>> sim.operation_statistics()['X']
    0
```

## Simulator.counting_operations
```
Whether operation execution statistics are recorded during `do(...)`.

Note that recording operation counts incurs per-instruction counter
overhead (~2-4x on fast gates), so this must be set when
constructing the `km.Simulator`.

Examples:
    >>> import kickmix as km
    >>> km.Simulator(4).counting_operations
    False
    >>> km.Simulator(4, counting_operations=True).counting_operations
    True
```

## Simulator.debug_print
```
@signature def debug_print(self) -> bool | Callable[[km.q | km.b | None, np.ndarray, km.b | None, np.ndarray], None]:
Controls how `DEBUG_PRINT` instructions are handled during `do(...)`.

Can be set to `True` (stderr), `False` (ignore), or a callback
`Callable[[km.q | km.b | None, np.ndarray, km.b | None, np.ndarray], None]`
receiving `(target, target_vals, condition, condition_vals)`.

Examples:
    >>> import kickmix as km
    >>> events = []
    >>> sim = km.Simulator(
    ...     batch_size=4,
    ...     debug_print=lambda t, tv, c, cv: events.append(
    ...         (t, tv.tolist(), c, cv.tolist())
    ...     ),
    ... )
    >>> sim.write_across_shots(km.b(0), 0b0101)
    >>> sim.do(km.Circuit('''
    ...     X q0
    ...     DEBUG_PRINT q0 if b0
    ...     DEBUG_PRINT
    ... '''))
    >>> events[0]
    (km.q(0), [True, True, True, True], km.b(0), [True, False, True, False])
    >>> events[1]
    (None, [False, False, False, False], None, [True, True, True, True])
```

## Simulator.do
```
do(self: kickmix.Simulator, circuit: kickmix.Circuit) -> None

@signature def do(self, circuit: km.Circuit) -> None:
Applies the instructions from the circuit to the simulator's state.

Args:
    circuit: The circuit with instructions to apply.

Examples:
    >>> import kickmix as km
    >>> import numpy as np
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.write_across_shots(km.q(0), np.array([False, True, False, True]))
    >>> sim.write_across_shots(km.q(1), np.array([False, False, True, True]))

    >>> sim.read_across_shots(km.q(0))
    array([False,  True, False,  True])
    >>> sim.read_across_shots(km.q(1))
    array([False, False,  True,  True])

    >>> sim.do(km.Circuit('''
    ...     CX q0 q1
    ...     X q0
    ... '''))

    >>> sim.read_across_shots(km.q(0))
    array([ True, False,  True, False])
    >>> sim.read_across_shots(km.q(1))
    array([False,  True,  True, False])
```

## Simulator.operation_statistics
```
operation_statistics(self: kickmix.Simulator, shot_index: Optional[int] = None) -> kickmix.OperationStatistics

@signature def operation_statistics(self, shot_index: int | None = None) -> km.OperationStatistics:
Returns operation statistics recorded during `do(...)`.

Conditional operations (such as `CCX q0 q1 q2 if b3` or operations
inside `PUSH_CONDITION` / `POP_CONDITION` blocks) are only counted
in shots where their condition was satisfied.

Args:
    shot_index: Optional index of a single shot in
        `range(sim.batch_size)`. If `None` (the default), returns
        the sum of operation counts across all `sim.batch_size`
        shots.

Returns:
    A `km.OperationStatistics` object containing operation counts
    and resource summaries (`num_instructions`, `num_toffoli_like`,
    `num_t_like`, `num_z_pow`, and
    `z_pow_clifford_hierarchy_counts`).

Raises:
    ValueError: Operation counting has not been enabled on this
        simulator.
    IndexError: `shot_index` is out of `range(sim.batch_size)`.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=4, counting_operations=True)
    >>> sim.write_across_shots(km.b(0), 0b0101)
    >>> sim.do(km.Circuit('''
    ...     X q0
    ...     CCX q0 q1 q2 if b0
    ...     Z_POW q0 0.25 if b0
    ...     Z_POW q0 0.125
    ... '''))
    >>> stats = sim.operation_statistics()
    >>> stats['X'], stats.num_toffoli_like, stats.num_t_like
    (4, 2, 2)
    >>> stats.num_z_pow(min_clifford_hierarchy_level=4)
    4
    >>> sim.operation_statistics(shot_index=0).num_toffoli_like
    1
    >>> sim.operation_statistics(shot_index=1).num_toffoli_like
    0
```

## Simulator.read_across_shots
```
read_across_shots(self: kickmix.Simulator, indices: object, *, out: object = None) -> object

@signature def read_across_shots(self, indices: km.q | km.b | bool | str | km.r | km.array | Sequence[km.q | km.b | bool], *, out: Any = None) -> np.ndarray | int | list[int]:
Reads the tracked values of the given qubits or bits across all shots.

Args:
    indices: The qubit id, bit id, or boolean constant to read, or
        an array/register of them (such as a register name `str`,
        `km.r`, `km.array`, or sequence).
    out: Where to store the output. Defaults to None (allocate a new
        numpy array). Can be set to a numpy array (with
        `dtype=np.bool_`) to write the results into, or to `int` to
        return the results bit-packed across shots in little-endian
        order.

Returns:
    If `indices` is a single qubit, bit, or bool: a 1D numpy bool
    array of shape `(sim.batch_size,)`, or a single bit-packed `int`
    if `out=int`.
    If `indices` is a register or sequence of length n: a 2D numpy
    bool array of shape `(n, sim.batch_size)`, or a `list` of n
    bit-packed `int`s if `out=int`.

Raises:
    IndexError: A register name or id is not found in the simulator.
    TypeError: `indices` cannot be converted to qubit ids, bit ids,
        or booleans.
    ValueError: `out` is not None, `int`, or a numpy bool array of
        the expected shape.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.write_across_shots(km.q(0), 0b1010)
    >>> sim.write_across_shots(km.q(1), 0b1100)
    >>> sim.read_across_shots(km.q(0))
    array([False,  True, False,  True])
    >>> sim.read_across_shots(km.q(0), out=int)
    10
    >>> sim.read_across_shots([km.q(0), km.q(1)], out=int)
    [10, 12]
```

## Simulator.read_phase_flipped_across_shots
```
read_phase_flipped_across_shots(self: kickmix.Simulator, *, out: object = None) -> object

@signature def read_phase_flipped_across_shots(self, *, out: Any = None) -> np.ndarray | int:
Reads whether or not each shot is phase flipped.

A shot is considered phase flipped if its tracked phase is closer to a
half turn than to no turns.

Args:
    out: Where to store the output. Defaults to None (allocate a new numpy
        array). Can be set to a numpy array to write the results into, or
        to `int` to return the result bit packed into an integer.

Returns:
    The phase flip information.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.write_across_shots(km.q(0), 0b1010)
    >>> sim.do(km.Circuit('Z q0'))
    >>> sim.read_phase_flipped_across_shots()
    array([False,  True, False,  True])
    >>> sim.read_phase_flipped_across_shots(out=int)
    10
```

## Simulator.read_shot_phase
```
read_shot_phase(self: kickmix.Simulator, shot_index: int) -> object

@signature def read_shot_phase(self, shot_index: int) -> int | fractions.Fraction:
Returns the tracked global phase of a shot.

The phase is affected by operations like Z, HMR, and Z_POW.

Returns:
    The phase, in half turns, as an int or as a `fractions.Fraction`.

    If the shot is exactly unphased (0 radians), the int 0 is returned.
    If the shot is exactly phase flipped (pi radians), the int 1 is returned.
    If the phase is some other value, a fractions.Fraction with the exact
    phase value (in half turns) is returned.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=5)
    >>> sim.read_shot_phase(shot_index=4)
    0

    >>> sim.do(km.Circuit('''
    ...     X q0
    ...     Z q0
    ... '''))
    >>> sim.read_shot_phase(shot_index=4)
    1

    >>> sim.do(km.Circuit('''
    ...     Z_POW q0 1.25000000000000001387778780781445675529539585113525390625
    ... '''))
    >>> sim.read_shot_phase(shot_index=4)
    Fraction(18014398509481985, 72057594037927936)
```

## Simulator.read_within_shot
```
read_within_shot(self: kickmix.Simulator, indices: object, shot_index: object, *, out: object = None) -> object

@signature def read_within_shot(self, indices: km.q | km.b | bool | str | km.r | km.array | Sequence[km.q | km.b | bool], shot_index: int, *, out: Any = None) -> np.ndarray | int | bool:
Reads the tracked values of the given qubits or bits within a single shot.

Args:
    indices: The qubit id, bit id, or boolean constant to read, or
        an array/register of them (such as a register name `str`,
        `km.r`, `km.array`, or sequence).
    shot_index: The index of the shot to read from, in
        `range(sim.batch_size)`.
    out: Where to store the output. Defaults to None (allocate a new
        numpy array). Can be set to a numpy array (with
        `dtype=np.bool_`) to write the results into, or to `int` to
        return the result as a `bool` (for a single item) or a
        little-endian bit-packed `int` (for a register or sequence).

Returns:
    If `indices` is a single qubit, bit, or bool: a 0D numpy bool
    array, or a `bool` if `out=int`.
    If `indices` is a register or sequence of length n: a 1D numpy
    bool array of shape `(n,)`, or a little-endian `int` in
    `range(2**n)` if `out=int`.

Raises:
    IndexError: `shot_index` is out of range, or a register name or
        id is not found in the simulator.
    TypeError: `indices` cannot be converted to qubit ids, bit ids,
        or booleans.
    ValueError: `out` is not None, `int`, or a numpy bool array of
        the expected shape.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> reg = builder.create_quantum_register(4, name='reg')
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=2)
    >>> sim.use_same_registers_as(circuit)
    >>> sim.write_within_shot('reg', 1, 0b1101)
    >>> sim.read_within_shot('reg', 1)
    array([ True, False,  True,  True])
    >>> sim.read_within_shot('reg', 1, out=int)
    13
```

## Simulator.use_same_registers_as
```
use_same_registers_as(self: kickmix.Simulator, circuit: kickmix.Circuit) -> None

@signature def use_same_registers_as(self, circuit: km.Circuit) -> None:
Copies register definitions from a circuit into the simulator.

After calling this method, registers defined in the circuit can be
referenced by name (`str`) or register id (`km.r`) when calling
`read_within_shot`, `write_within_shot`, `read_across_shots`, and
`write_across_shots`.

Args:
    circuit: The circuit whose register definitions should be copied.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> reg = builder.create_quantum_register(3, name='data')
    >>> builder.x(reg[0])
    >>> builder.x(reg[2])
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=2)
    >>> sim.use_same_registers_as(circuit)
    >>> sim.do(circuit)
    >>> sim.read_within_shot('data', 0, out=int)
    5
```

## Simulator.write_across_shots
```
write_across_shots(self: kickmix.Simulator, index: object, new_value: object) -> None

@signature def write_across_shots(self, index: km.q | km.b | str | km.r | km.array | Sequence[km.q | km.b], new_value: int | Sequence[int] | np.ndarray) -> None:
Sets the tracked value of the given qubits or bits, across all shots.

Args:
    index: The qubit id or bit id to write to, or an array of them
        (e.g. a register name).
    new_value: The value to write.

        If `index` is a single qubit or bit, this is an `int` or an
        `np.ndarray` with dtype=np.bool_ and shape=(sim.batch_size,).

        If `index` is an array of length n, this is a sequence of n
        `int`s or an `np.ndarray` with dtype=np.bool_ and
        shape=(n, sim.batch_size).

        Each `int` is bit packed in little-endian order, so the bit
        for shot k is `(new_value >> k) & 1`. This matches the
        layout returned by `read_across_shots(..., out=int)`.

Raises:
    IndexError: The given index isn't a qubit id or bit id.
    ValueError: The given new_value isn't valid.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=4)
    >>> sim.write_across_shots(km.q(0), 0b1010)
    >>> sim.read_across_shots(km.q(0))
    array([False,  True, False,  True])
    >>> sim.read_across_shots(km.q(0), out=int)
    10
```

## Simulator.write_shot_phase
```
write_shot_phase(self: kickmix.Simulator, shot_index: int, new_phase_half_turns: object) -> None

@signature def write_shot_phase(self, shot_index: int, new_phase_half_turns: int | float | fractions.Fraction | str) -> None:
Sets the tracked global phase of a shot.

The phase is affected by operations like Z, HMR, and Z_POW.

Args:
    shot_index: The shot whose phase is being written.
    new_phase_half_turns: The new phase, as a rotation in half turn units.
        This can be an int, a float, or a fractions.Fraction.
        The value will be canonicalized into the range [0, 2) and then
        rounded to the nearest multiple of 2**-127.

Examples:
    >>> import kickmix as km
    >>> sim = km.Simulator(batch_size=5)

    >>> sim.write_shot_phase(4, 0.125)
    >>> sim.read_shot_phase(4)
    Fraction(1, 8)

    >>> sim.write_shot_phase(4, 1.0)
    >>> sim.read_shot_phase(4)
    1
```

## Simulator.write_within_shot
```
write_within_shot(self: kickmix.Simulator, index: object, shot_index: object, new_value: object) -> None

@signature def write_within_shot(self, index: km.q | km.b | str | km.r | km.array | Sequence[km.q | km.b], shot_index: int, new_value: int | bool | np.ndarray) -> None:
Sets the tracked values of the given qubits or bits within a single shot.

Args:
    index: The qubit id or bit id to write to, or an array of them
        (e.g. a register name).
    shot_index: The index of the shot to write to, in
        `range(sim.batch_size)`.
    new_value: The value to write. Can be an `int` (or `bool`) in
        `range(2**n)` bit-packed in little-endian order, or a 1D
        `np.ndarray` with `dtype=np.bool_` and shape `(n,)`, where
        n is the number of targeted qubits or bits.

Raises:
    IndexError: `shot_index` is out of range, or the given `index`
        is not a valid qubit, bit, or register.
    ValueError: `new_value` is not a valid `int` or 1D numpy bool
        array of the expected range or shape.

Examples:
    >>> import kickmix as km
    >>> builder = km.CircuitBuilder()
    >>> reg = builder.create_quantum_register(4, name='reg')
    >>> circuit = builder.finish_circuit()
    >>> sim = km.Simulator(batch_size=2)
    >>> sim.use_same_registers_as(circuit)
    >>> sim.write_within_shot('reg', 0, 0b1011)
    >>> sim.read_within_shot('reg', 0, out=int)
    11
```
