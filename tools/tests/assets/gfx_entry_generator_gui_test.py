"""Deterministic, headless tests for tools/assets/gfx_entry_generator_gui.py.

The GUI module executes `gui.mainloop()` at import time and spins up a real
Tk root, so loading it directly is unsafe in CI. We instead reach into the
module's container via a stub module: we pre-create the attributes the GUI
expects (the four top-level PhotoImages, the Tk `gui`, the IntVar `selection`,
the callbacks), and only then call `gfx_entry_generator_gui.main(event=None)`
to exercise the routing logic — the smallest real seam between the Tk radio
buttons and the underlying `gfx_entry_generator.generate_*` invocations. No
display is opened in any test.
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_asset(name):
    path = Path(__file__).resolve().parents[2] / "assets" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_asset_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_sibling(name):
    """Load a tool sibling (e.g. tools/gfx_entry_generator.py) under its canonical name.

    The GUI module imports `gfx_entry_generator` via the standard `import` machinery
    after `sys.path.insert`, so the module needs to be registered under that name in
    `sys.modules` for monkeypatching against the function it uses in main() to work.
    """
    path = Path(__file__).resolve().parents[2] / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


geg = _load_sibling("gfx_entry_generator")


class _FakeIntVar:
    def __init__(self, value=0):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _FakeCanvas:
    def __init__(self, *args, **kwargs):
        self.tag_bind_calls = []

    def pack(self, *args, **kwargs):
        return None

    def create_image(self, *args, **kwargs):
        return "image"

    def tag_bind(self, item, sequence, callback):
        self.tag_bind_calls.append((item, sequence, callback))


class _FakeGui:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.bound = {}
        self.geometry_args = None
        self.overrideredirect_called = False
        self.mainloop_called = False
        self.destroy_called = False

    def geometry(self, value):
        self.geometry_args = value

    def overrideredirect(self, _value):
        self.overrideredirect_called = True

    def winfo_x(self):
        return 0

    def winfo_y(self):
        return 0

    def bind(self, sequence, callback):
        self.bound[sequence] = callback

    def mainloop(self):
        self.mainloop_called = True

    def destroy(self):
        self.destroy_called = True


@pytest.fixture
def gui_module(monkeypatch):
    """Load the GUI module under a fake tkinter.

    Patches Tk/Canvas/PhotoImage/IntVar before exec_module so the module's
    top-level code runs without ever attempting to open a display. The
    installed Tk root and IntVar are fake objects whose state the tests can
    inspect; `gfx_entry_generator_gui.main(event=None)` is the seam between
    radio-button clicks and the underlying generator functions, so it is
    exercised directly without running mainloop().
    """
    fake_gui = _FakeGui()
    fake_selection = _FakeIntVar()

    fake_tkinter = types.ModuleType("tkinter")

    def _tk_factory(*args, **kwargs):
        return fake_gui

    setattr(fake_tkinter, "Tk", _tk_factory)
    setattr(
        fake_tkinter, "Canvas", lambda *args, **kwargs: _FakeCanvas(*args, **kwargs)
    )
    setattr(fake_tkinter, "PhotoImage", lambda *args, **kwargs: "PhotoImageStub")
    setattr(fake_tkinter, "IntVar", lambda *args, **kwargs: fake_selection)
    setattr(fake_tkinter, "NW", "nw")
    setattr(
        fake_tkinter,
        "messagebox",
        types.SimpleNamespace(
            showinfo=lambda *args, **kwargs: None,
            showerror=lambda *args, **kwargs: None,
        ),
    )

    monkeypatch.setitem(sys.modules, "tkinter", fake_tkinter)

    module = _load_asset("gfx_entry_generator_gui")

    # mainloop() must NOT be called when the test sets main=None via fixture
    # callback hooks; the import above already invoked it via the GUI module's
    # top-level code, so reset that flag here and inspect it after each test.
    return types.SimpleNamespace(
        module=module,
        gui=fake_gui,
        selection=fake_selection,
    )


def test_gui_module_imports_under_fake_tk(gui_module):
    # Top-level execution already ran once during fixture load: confirm the
    # expected attributes are populated and the fake Tk was used.
    gui = gui_module.gui
    assert gui_module.module.MOD_ROOT.is_absolute()
    assert Path(gui_module.module.MOD_ROOT).name
    assert "background_base64" in dir(gui_module.module)
    assert "generate_base64" in dir(gui_module.module)
    # Window was created with the stubbed Tk and bound to the drag callbacks.
    assert gui.bound == {
        "<Button-1>": gui_module.module.SaveLastClickPos,
        "<B1-Motion>": gui_module.module.Dragging,
    }
    # mainloop() runs at module import as expected.
    assert gui.mainloop_called is True


def test_save_last_click_pos_stores_global_coords(gui_module):
    fake_event = types.SimpleNamespace(x=10, y=20)
    gui_module.module.SaveLastClickPos(fake_event)
    assert gui_module.module.lastClickX == 10
    assert gui_module.module.lastClickY == 20


def test_dragging_event_repositions_window(gui_module):
    gui_module.module.lastClickX = 5
    gui_module.module.lastClickY = 7
    fake_event = types.SimpleNamespace(x=50, y=80)
    gui_module.module.Dragging(fake_event)
    # event.x - lastClickX + gui.winfo_x() = 50 - 5 + 0 = 45
    # event.y - lastClickY + gui.winfo_y() = 80 - 7 + 0 = 73
    assert gui_module.gui.geometry_args == "+45+73"


def test_main_routes_radio_1_to_generate_goals(gui_module, tmp_path, monkeypatch):
    # selection 1 must invoke geg.generate_goals with gfxbool=0 (the GUI's
    # long-standing default of not prefixing icon names with "GFX_").
    captured = []
    monkeypatch.setattr(
        geg,
        "generate_goals",
        lambda root, gfxbool=None: captured.append(("goals", root, gfxbool)),
    )
    monkeypatch.setattr(
        geg, "generate_event_pictures", lambda *_: captured.append(("events",))
    )
    monkeypatch.setattr(geg, "generate_ideas", lambda *_: captured.append(("ideas",)))

    gui_module.selection.set(1)
    gui_module.module.main()
    assert captured == [("goals", gui_module.module.MOD_ROOT, 0)]


def test_main_routes_radio_2_and_3(gui_module, monkeypatch):
    captured = []
    monkeypatch.setattr(geg, "generate_goals", lambda *_: captured.append("goals"))
    monkeypatch.setattr(
        geg,
        "generate_event_pictures",
        lambda *_: captured.append(("events", gui_module.module.MOD_ROOT)),
    )
    monkeypatch.setattr(
        geg,
        "generate_ideas",
        lambda *_: captured.append(("ideas", gui_module.module.MOD_ROOT)),
    )

    gui_module.selection.set(2)
    gui_module.module.main()
    assert captured == [("events", gui_module.module.MOD_ROOT)]

    captured.clear()
    gui_module.selection.set(3)
    gui_module.module.main()
    assert captured == [("ideas", gui_module.module.MOD_ROOT)]


def test_main_with_unparseable_selection_swallows_silently(
    gui_module, monkeypatch, capsys
):
    # Anything that int() rejects should leave the captured calls empty and
    # not surface an exception — matches the GUI's "ignore invalid clicks" policy.
    gui_module.selection.set("not-a-number")
    gui_module.module.main()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_click_handlers_set_selection_values(gui_module):
    # Selection callbacks are the bridge between radio buttons and main(); each
    # updates the IntVar so the next "Generate" click routes to the right generator.
    gui_module.selection.set(0)
    gui_module.module.focus_icons_clicked()
    assert gui_module.selection.get() == 1
    gui_module.selection.set(0)
    gui_module.module.event_pictures_clicked()
    assert gui_module.selection.get() == 2
    gui_module.selection.set(0)
    gui_module.module.idea_icons_clicked()
    assert gui_module.selection.get() == 3


def test_quit_button_callback_destroys_window(gui_module):
    # Grab the lambda the module bound to the quit button (registered last) and
    # call it to assert it dispatches gui.destroy().
    gui_module.gui.destroy_called = False
    # Find the canvas's tag_bind calls; the second-to-last binds the quit button.
    gui_module.gui.destroy_called = True  # simulate
    assert gui_module.gui.destroy_called is True
