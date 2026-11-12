"""Shared settings for the 3D model tools.

`audit_models.py` and `optimize_mesh.py` both read these, so a model is checked
and optimized against the same numbers. The triangle targets and texture rules
mirror docs/src/content/resources/3d-model-performance-guidelines.md; change
both together.
"""

# Folder under gfx/models/units -> triangle target for the rendered meshes.
TRIANGLE_TARGETS = (
    ("/weapons/", 1000),
    ("/tanks/", 5000),
    ("/vehicles/", 5000),
    ("/ships/", 8000),
    ("/planes/", 6000),
)

# A mesh below this many triangles is never simplified.
MIN_TRIANGLES = 1000

# The simplifier stops at the triangle target or at this error, whichever comes
# first. The error is a share of the mesh's own extent.
ERROR_CEILING = 0.005
ERROR_CEILINGS = (("/weapons/", 0.01),)

# No point of the simplified surface may sit farther than this from the
# original, and the reverse. A share of the whole model's diagonal.
GUARD_TOLERANCE = 0.01
GUARD_ATTEMPTS = 6

# Split vertices that share position, UVs and skinning are merged when their
# normals differ by less than this.
WELD_ANGLE_DEGREES = 20.0

# Model textures: compressed DDS with mipmaps, power-of-two, at most this size.
MAX_TEXTURE_SIZE = 2048

# Mipmaps only pay off on textures drawn well below their full size. That is the
# 3D map: unit and building models and particles. GUI art is drawn at full size,
# so a chain there only adds a third to the file and to video memory.
MIPMAP_NEEDED = "needed"
MIPMAP_NONE = "none"
MIPMAP_KEEP = "keep"
MIPMAP_RULES = (
    ("/gfx/models/", MIPMAP_NEEDED),
    ("/gfx/particles/", MIPMAP_NEEDED),
    # Terrain, fonts and map arrows mirror vanilla's layout: leave them as they are.
    ("/map/", MIPMAP_KEEP),
    ("/gfx/fonts/", MIPMAP_KEEP),
    ("/gfx/maparrows/", MIPMAP_KEEP),
    ("/gfx/", MIPMAP_NONE),
)


def _lookup(table, rel_path, default):
    path = "/" + rel_path.replace("\\", "/").lower()
    for folder, value in table:
        if folder in path:
            return value
    return default


def triangle_target(rel_path):
    """Triangle target for a mesh path, or None when the standard sets none."""
    return _lookup(TRIANGLE_TARGETS, rel_path, None)


def error_ceiling(rel_path):
    """Simplification error ceiling for a mesh path."""
    return _lookup(ERROR_CEILINGS, rel_path, ERROR_CEILING)


def mipmap_rule(rel_path):
    """Whether a texture path should carry mipmaps: needed, none or keep."""
    return _lookup(MIPMAP_RULES, rel_path, MIPMAP_KEEP)
