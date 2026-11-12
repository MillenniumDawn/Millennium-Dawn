"""Read and write Paradox binary `.mesh` files.

The file is `@@b@` followed by objects and properties. An object is a run of
`[` (its depth) and a NUL-terminated name. A property is `!`, a length-prefixed
name, a type byte and a u32 count: `i` and `f` hold 4-byte values, `s` holds
u32-length strings. A file round-trips byte for byte through parse and write.
"""

import struct
from dataclasses import dataclass, field
from typing import Iterator, Optional

import numpy as np

HEADER = b"@@b@"
# Per-vertex arrays on a mesh node and their width.
VERTEX_ATTRS = {"p": 3, "n": 3, "ta": 4, "u0": 2, "u1": 2, "u2": 2, "u3": 2}


class MeshParseError(ValueError):
    pass


@dataclass
class Node:
    name: str
    depth: int
    # property name -> (type char, ndarray for i/f or list of bytes for s)
    props: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def child(self, name: str) -> Optional["Node"]:
        return next((c for c in self.children if c.name == name), None)


@dataclass
class MeshPart:
    shape: Node
    mesh: Node
    skin: Optional[Node]
    joints: int
    root_joint: int

    @property
    def shader(self) -> str:
        material = self.mesh.child("material")
        if material is None or "shader" not in material.props:
            return ""
        return material.props["shader"][1][0].rstrip(b"\0").decode("latin-1")

    @property
    def rendered(self) -> bool:
        return self.shader.lower() != "collision"

    @property
    def triangles(self) -> int:
        return self.mesh.props["tri"][1].size // 3


def _parse_property(data: bytes, pos: int, node: Node) -> int:
    length = data[pos + 1]
    name = data[pos + 2 : pos + 2 + length].decode("latin-1")
    pos += 2 + length
    kind = chr(data[pos])
    (count,) = struct.unpack_from("<I", data, pos + 1)
    pos += 5
    if kind in "if":
        node.props[name] = (kind, np.frombuffer(data, "<" + kind + "4", count, pos))
        return pos + 4 * count
    if kind != "s":
        raise MeshParseError(f"unknown property type {kind!r} at byte {pos}")
    values = []
    for _ in range(count):
        size = int.from_bytes(data[pos : pos + 4], "little")
        values.append(data[pos + 4 : pos + 4 + size])
        pos += 4 + size
    if pos > len(data):
        raise MeshParseError(f"string property {name!r} runs past the end")
    node.props[name] = (kind, values)
    return pos


def parse(data: bytes) -> Node:
    """Parse a mesh file into a tree. The root node holds the top-level items."""
    if not data.startswith(HEADER):
        raise MeshParseError("missing @@b@ header")
    root = Node("", 0)
    stack = [root]
    pos, end = len(HEADER), len(data)
    try:
        while pos < end:
            marker = data[pos]
            if marker == ord("!"):
                pos = _parse_property(data, pos, stack[-1])
            elif marker == ord("["):
                depth = 0
                while data[pos] == ord("["):
                    depth += 1
                    pos += 1
                stop = data.index(b"\0", pos)
                node = Node(data[pos:stop].decode("latin-1"), depth)
                pos = stop + 1
                while stack[-1].depth >= depth:
                    stack.pop()
                stack[-1].children.append(node)
                stack.append(node)
            else:
                raise MeshParseError(f"unexpected byte {marker:#x} at {pos}")
    except (struct.error, IndexError, ValueError) as exc:
        if isinstance(exc, MeshParseError):
            raise
        raise MeshParseError(f"truncated or corrupt data near byte {pos}") from exc
    return root


def write(root: Node) -> bytes:
    """Serialize a tree produced by `parse`."""
    out = bytearray(HEADER)

    def emit(node: Node) -> None:
        for name, (kind, value) in node.props.items():
            encoded = name.encode("latin-1")
            out.extend(b"!" + bytes([len(encoded)]) + encoded + kind.encode())
            if kind == "s":
                out.extend(struct.pack("<I", len(value)))
                for text in value:
                    out.extend(struct.pack("<I", len(text)) + text)
            else:
                array = np.asarray(value, "<" + kind + "4")
                out.extend(struct.pack("<I", array.size) + array.tobytes())
        for child in node.children:
            out.extend(b"[" * child.depth + child.name.encode("latin-1") + b"\0")
            emit(child)

    emit(root)
    return bytes(out)


def walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from walk(child)


def mesh_parts(root: Node) -> list:
    """Every mesh that has geometry, in file order, with its skin and skeleton size."""
    parts = []
    for shape in walk(root):
        skeleton = shape.child("skeleton")
        joints = skeleton.children if skeleton else []
        roots = [
            int(j.props["ix"][1][0])
            for j in joints
            if "pa" not in j.props and "ix" in j.props
        ]
        for mesh in shape.children:
            if mesh.name == "mesh" and "p" in mesh.props and "tri" in mesh.props:
                parts.append(
                    MeshPart(
                        shape,
                        mesh,
                        mesh.child("skin"),
                        len(joints),
                        roots[0] if roots else 0,
                    )
                )
    return parts
