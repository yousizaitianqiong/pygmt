"""
Test pygmt.config.
"""

import re

import pytest
from pygmt import Figure, config
from pygmt.clib import Session
from pygmt.params import Axis, Frame


def _get_defaults(*keys):
    """
    Read settings for the current figure.
    """
    with Session() as lib:
        return [lib.get_default(key) for key in keys]


def test_config_restores_automatic_frame_pen_width():
    """
    Restore the automatic frame pen width after a temporary explicit width.
    """
    Figure()
    initial = _get_defaults("MAP_FRAME_PEN")
    with config(MAP_FRAME_PEN="4p,blue"):
        assert _get_defaults("MAP_FRAME_PEN") == ["4p,blue"]
    assert _get_defaults("MAP_FRAME_PEN") == initial


@pytest.mark.parametrize(
    ("initial", "temporary", "expected"),
    [
        ("2.25p,red", "4p,blue,5_3:1p", r"2\.25p,red"),
        ("auto,darkred,7_4:1p", "4p,blue,solid", r"darkred,7_4:1p(?::0p)*"),
    ],
    ids=["explicit-solid", "automatic-dashes"],
)
def test_config_restores_frame_pen_style(initial, temporary, expected):
    """
    Restore both solid and dashed frame pens after changing their line styles.
    """
    Figure()
    config(MAP_FRAME_PEN=initial)
    assert re.fullmatch(expected, _get_defaults("MAP_FRAME_PEN")[0])
    with config(MAP_FRAME_PEN=temporary):
        assert "blue" in _get_defaults("MAP_FRAME_PEN")[0]
    # GMT can append extra phase suffixes when reloading an automatic-width pen.
    assert re.fullmatch(expected, _get_defaults("MAP_FRAME_PEN")[0])


@pytest.mark.parametrize("group", ["MAP_GRID_PEN", "MAP_TICK_PEN"])
def test_config_restores_pen_group(group):
    """
    Restore distinct primary and secondary pens across nested contexts.
    """
    Figure()
    primary, secondary = f"{group}_PRIMARY", f"{group}_SECONDARY"
    config(**{primary: "2.25p,red", secondary: "auto,green"})
    assert _get_defaults(primary, secondary) == ["2.25p,red", "green"]
    with config(**{group: "4.25p,blue"}):
        assert _get_defaults(primary, secondary) == ["4.25p,blue"] * 2
        with pytest.raises(ZeroDivisionError), config(**{group: "6.25p,orange"}):
            raise ZeroDivisionError
        assert _get_defaults(primary, secondary) == ["4.25p,blue"] * 2
    assert _get_defaults(primary, secondary) == ["2.25p,red", "green"]


@pytest.mark.parametrize(
    ("initial", "color", "expected"),
    [
        ("2.25p,red", "blue", r"2\.25p,blue"),
        ("auto,red,dashed", "blue", r"blue,dashed(?::0p)+"),
    ],
    ids=["explicit-width", "automatic-dashes"],
)
def test_config_updates_only_pen_color(initial, color, expected):
    """
    Apply a direct color-only update without changing the width or style.
    """
    Figure()
    config(MAP_FRAME_PEN=initial)
    config(MAP_FRAME_PEN=color)
    assert re.fullmatch(expected, _get_defaults("MAP_FRAME_PEN")[0])


def test_config_restores_map_default_pen_colors():
    """
    Restore the pens recolored by a plus-prefixed MAP_DEFAULT_PEN.
    """
    Figure()
    keys = (
        "MAP_DEFAULT_PEN",
        "MAP_FRAME_PEN",
        "MAP_GRID_PEN_PRIMARY",
        "MAP_GRID_PEN_SECONDARY",
        "MAP_TICK_PEN_PRIMARY",
        "MAP_TICK_PEN_SECONDARY",
    )
    config(MAP_FRAME_PEN="2.25p,red", MAP_GRID_PEN_PRIMARY="0.8p,darkgreen")
    initial = _get_defaults(*keys)
    with config(MAP_DEFAULT_PEN="+1.25p,blue"):
        assert all(pen.endswith("blue") for pen in _get_defaults(*keys))
    assert _get_defaults(*keys) == initial


@pytest.mark.mpl_image_compare
def test_config():
    """
    Test if config works globally and locally.
    """
    fig = Figure()
    # Change global settings of current figure
    config(FONT_ANNOT_PRIMARY="blue")
    fig.basemap(
        region=[0, 10, 0, 10],
        projection="X5c/5c",
        frame=Frame(title="Blue Annotation", axis=Axis(annot=True, tick=True)),
    )

    with config(FONT_LABEL="red", FONT_ANNOT_PRIMARY="red"):
        fig.shift_origin(xshift="7c")
        fig.basemap(
            region=[0, 10, 0, 10],
            projection="X5c/5c",
            frame=Frame(
                title="red annotation",
                xaxis=Axis(annot=True, tick=True, label="red label"),
                yaxis=Axis(annot=True, tick=True),
            ),
        )

    fig.shift_origin(xshift="7c")
    fig.basemap(
        region=[0, 10, 0, 10],
        projection="X5c/5c",
        frame=Frame(title="Blue Annotation", axis=Axis(annot=True, tick=True)),
    )
    # Revert to default settings in current figure
    config(FONT_ANNOT_PRIMARY="black")
    return fig


@pytest.mark.mpl_image_compare
def test_config_font_one():
    """
    Test that setting FONT config changes all FONT_* settings except FONT_LOGO.

    Specifically, this test only checks that FONT_ANNOT_PRIMARY, FONT_ANNOT_SECONDARY,
    FONT_LABEL, and FONT_TITLE are modified.
    """
    fig = Figure()
    with config(FONT="8p,red"):
        fig.basemap(region=[0, 9, 0, 9], projection="C3/3/9c", compass="jTL+w3c+d4.5+l")
    fig.basemap(compass="jBR+w3.5c+d-4.5+l")
    return fig


@pytest.mark.mpl_image_compare
def test_config_font_annot():
    """
    Test that setting FONT_ANNOT config changes both FONT_ANNOT_PRIMARY and
    FONT_ANNOT_SECONDARY.
    """
    fig = Figure()
    with config(FONT_ANNOT="6p,red"):
        fig.basemap(region=[0, 9, 0, 9], projection="C3/3/9c", compass="jTL+w3c+d4.5")
    fig.basemap(compass="jBR+w3.5c+d-4.5")
    return fig


@pytest.mark.benchmark
@pytest.mark.mpl_image_compare
def test_config_format_date_map():
    """
    Test that setting FORMAT_DATE_MAP config changes how the output date string is
    plotted.

    Note the space in 'o dd', this acts as a regression test for
    https://github.com/GenericMappingTools/pygmt/issues/247.

    Setting FORMAT_DATE_MAP="yyyy mm dd" as a regression test for
    https://github.com/GenericMappingTools/pygmt/issues/2298.
    """
    fig = Figure()
    # Set FORMAT_DATE_MAP to "yyyy mm dd" which contains whitespaces.
    config(FORMAT_DATE_MAP="yyyy mm dd")
    with config(FORMAT_DATE_MAP="o dd"):
        fig.basemap(
            region=["1969-7-21T", "1969-7-23T", 0, 1],
            projection="X2.5c/0.1c",
            frame=Frame(axes="S", xaxis2=Axis(annot="1D")),
        )
    return fig


@pytest.mark.mpl_image_compare
def test_config_format_time_map():
    """
    Test that setting FORMAT_TIME_MAP config changes both FORMAT_TIME_PRIMARY_MAP and
    FORMAT_TIME_SECONDARY_MAP.
    """
    fig = Figure()
    with config(FORMAT_TIME_MAP="abbreviation"):
        fig.basemap(
            region=["2020-1-24T", "2020-1-27T", 0, 1],
            projection="X6c/1c",
            frame=Frame(axes="NWse", axis=Axis(annot="1K"), axis2=Axis(annot="1K")),
        )
    fig.basemap(frame=Frame(axes="nwSE", axis=Axis(annot="1K"), axis2=Axis(annot="1K")))
    return fig


@pytest.mark.mpl_image_compare
def test_config_map_annot_offset():
    """
    Test that setting MAP_ANNOT_OFFSET config changes both MAP_ANNOT_OFFSET_PRIMARY and
    MAP_ANNOT_OFFSET_SECONDARY.
    """
    fig = Figure()
    with config(MAP_ANNOT_OFFSET="15p"):
        fig.basemap(
            region=["2020-1-24T", "2020-1-27T", 0, 1],
            projection="X6c/1c",
            frame=Frame(axes="NWse", axis=Axis(annot="1d"), axis2=Axis(annot="1d")),
        )
    fig.basemap(frame=Frame(axes="nwSE", axis=Axis(annot="1d"), axis2=Axis(annot="1d")))
    return fig


@pytest.mark.mpl_image_compare
def test_config_map_grid_cross_size():
    """
    Test that setting MAP_GRID_CROSS_SIZE config changes both
    MAP_GRID_CROSS_SIZE_PRIMARY and MAP_GRID_CROSS_SIZE_SECONDARY.
    """
    fig = Figure()
    with config(MAP_GRID_CROSS_SIZE="3p"):
        fig.basemap(
            region=["2020-1-24T21:00", "2020-1-25T00:00", 0, 1],
            projection="X6c/2c",
            frame=Frame(
                axes="NWse",
                axis=Axis(annot="1H", grid=True),
                axis2=Axis(annot="45m", grid="45m"),
            ),
            verbose="error",
        )
    fig.shift_origin(yshift=-3)
    fig.basemap(
        frame=Frame(
            axes="nwSE",
            axis=Axis(annot="1H", grid=True),
            axis2=Axis(annot="45m", grid="45m"),
        ),
        verbose="error",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_config_map_grid_pen():
    """
    Test that setting MAP_GRID_PEN config changes both MAP_GRID_PEN_PRIMARY and
    MAP_GRID_PEN_SECONDARY.
    """
    fig = Figure()
    # Hold the line width fixed so this image checks the color change.
    config(MAP_GRID_PEN="thick")
    with config(MAP_GRID_PEN="thick,red"):
        fig.basemap(
            region=["2020-1-24T21:00", "2020-1-25T00:00", 0, 1],
            projection="X6c/2c",
            frame=Frame(
                axes="NWse",
                axis=Axis(annot="1H", grid=True),
                axis2=Axis(annot="45m", grid="45m"),
            ),
            verbose="error",
        )
    fig.shift_origin(yshift=-3)
    fig.basemap(
        frame=Frame(
            axes="nwSE",
            axis=Axis(annot="1H", grid=True),
            axis2=Axis(annot="45m", grid="45m"),
        ),
        verbose="error",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_config_map_tick_length():
    """
    Test that setting MAP_TICK_LENGTH config changes both MAP_TICK_LENGTH_PRIMARY and
    MAP_TICK_LENGTH_SECONDARY.
    """
    fig = Figure()
    with config(MAP_TICK_LENGTH="5p"):
        fig.basemap(
            region=["2020-1-24T21:00", "2020-1-25T00:00", 0, 1],
            projection="X6c/2c",
            frame=Frame(
                axes="NWse",
                axis=Axis(annot="1H", grid=True),
                axis2=Axis(annot="45m", grid="45m"),
            ),
            verbose="error",
        )
    fig.shift_origin(yshift=-3)
    fig.basemap(
        frame=Frame(
            axes="nwSE",
            axis=Axis(annot="1H", grid=True),
            axis2=Axis(annot="45m", grid="45m"),
        ),
        verbose="error",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_config_map_tick_pen():
    """
    Test that setting MAP_TICK_PEN config changes both MAP_TICK_PEN_PRIMARY and
    MAP_TICK_PEN_SECONDARY.
    """
    fig = Figure()
    # Hold the line width fixed so this image checks the color change.
    config(MAP_TICK_PEN="thick")
    with config(MAP_TICK_PEN="thick,red"):
        fig.basemap(
            region=["2020-1-24T21:00", "2020-1-25T00:00", 0, 1],
            projection="X6c/2c",
            frame=Frame(
                axes="NWse",
                axis=Axis(annot="1H", grid=True),
                axis2=Axis(annot="45m", grid="45m"),
            ),
            verbose="error",
        )
    fig.shift_origin(yshift=-3)
    fig.basemap(
        frame=Frame(
            axes="nwSE",
            axis=Axis(annot="1H", grid=True),
            axis2=Axis(annot="45m", grid="45m"),
        ),
        verbose="error",
    )
    return fig


def test_config_ps_convert():
    """
    Test that Parameter 'PS_CONVERT' is not supported.
    """
    # Check that PS_CONVERT is removed from the autocomplete list
    assert "PS_CONVERT" not in config._keywords

    # Check that a warning is raised when PS_CONVERT is used in config
    msg = (
        "Parameter 'PS_CONVERT' is not supported. "
        "To configure conversion options, please pass parameters to "
        "pygmt.Figure.savefig or pygmt.Figure.show instead."
    )
    with pytest.warns(SyntaxWarning, match=msg):
        config(PS_CONVERT="C")
