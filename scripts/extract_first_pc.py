#!/usr/bin/env python3
"""Extract the "First PC" dataset into a Python-friendly format.

The binary files used by the original WebGL viewer follow the layout
produced by :func:`NParray.fromURL` in ``index.html``:

* uint32 dtype index (see ``dtypeMap`` in ``index.html``)
* uint32 number of dimensions
* ``ndim`` uint32 values with the array shape
* the remaining bytes as the array payload in the requested dtype

This script mirrors that logic and exports the decoded values to JSON so
that they can be loaded easily from Python for plotting or analysis.
"""

from __future__ import annotations

import argparse
import json
import struct
from array import array
from pathlib import Path
from typing import Tuple

# Mapping of dtype indices used by the viewer to Python ``array`` typecodes
# and human readable names.  See ``dtypeMap`` in ``index.html``.
DTYPE_MAP = {
    0: ("I", "uint32"),
    1: ("H", "uint16"),
    2: ("B", "uint8"),
    3: ("i", "int32"),
    4: ("h", "int16"),
    5: ("b", "int8"),
    6: ("f", "float32"),
}

def load_nparray(path: Path) -> Tuple[str, Tuple[int, ...], array]:
    """Load an ``NParray`` binary file.

    Parameters
    ----------
    path:
        Path to the ``.bin`` file.

    Returns
    -------
    tuple
        ``(dtype_name, shape, data_array)`` where ``data_array`` is an
        instance of :class:`array.array` with the correct type code.
    """

    with path.open("rb") as fh:
        header = fh.read(8)
        if len(header) != 8:
            raise ValueError("File is too small to contain an NParray header")
        dtype_idx, ndim = struct.unpack("<II", header)
        if dtype_idx not in DTYPE_MAP:
            raise ValueError(f"Unsupported dtype index {dtype_idx}")
        typecode, dtype_name = DTYPE_MAP[dtype_idx]

        shape_bytes = fh.read(4 * ndim)
        if len(shape_bytes) != 4 * ndim:
            raise ValueError("Truncated shape information in header")
        if ndim:
            shape = struct.unpack(f"<{ndim}I", shape_bytes)
        else:
            shape = tuple()

        header_bytes = (ndim + 2) * 4
        total_bytes = path.stat().st_size
        data_bytes = total_bytes - header_bytes
        itemsize = array(typecode).itemsize
        if data_bytes % itemsize:
            raise ValueError(
                f"File size {total_bytes} is not compatible with dtype '{dtype_name}'"
            )

        expected_values = data_bytes // itemsize
        data = array(typecode)
        if expected_values:
            data.fromfile(fh, expected_values)

        remainder = fh.read(1)
        if remainder:
            raise ValueError("Unexpected extra bytes at end of file")

    return dtype_name, shape, data


def export_to_json(dtype_name: str, shape: Tuple[int, ...], data: array, output: Path) -> None:
    """Write the decoded array to a JSON file."""

    payload = {
        "dtype": dtype_name,
        "shape": list(shape),
        "data": list(data),
    }
    with output.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("First PC.bin"),
        help="Path to the First PC binary file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("first_pc.json"),
        help="Where to store the exported JSON data.",
    )
    args = parser.parse_args()

    dtype_name, shape, data = load_nparray(args.input)
    export_to_json(dtype_name, shape, data, args.output)
    print(f"Decoded {args.input} -> {args.output} ({dtype_name}, shape={shape}, values={len(data)})")


if __name__ == "__main__":
    main()
