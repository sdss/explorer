"""Plot themes"""

from bokeh.themes import Theme

__all__ = ["darkprops", "lightprops", "DARKTHEME", "LIGHTTHEME"]

darkprops = {
    "Plot": {
        "background_fill_color": "#212121",  # grey-darken-3
        "border_fill_color": "#424242",
        "outline_line_color": "#616161",  # darken-2
    },
    "Axis": {
        "major_tick_line_color": "#FFFFFF",  # White ticks for contrast
        "minor_tick_line_color": "#BDBDBD",  # grey-lighten-1
        "axis_line_color": "#BDBDBD",
        "major_label_text_color": "#FFFFFF",  # White for labels
        "major_label_text_font_size": "11pt",
        "axis_label_text_color": "#FFFFFF",  # White for labels
        "axis_label_text_font_size": "16pt",
    },
    "Grid": {
        "grid_line_color": "#616161",  # grey-darken-2 (x/y grid)
    },
    "Title": {
        "text_color": "#FFFFFF",  # White text
        "text_font_size": "16pt",
    },
    "Legend": {
        "background_fill_color": "#424242",
        "label_text_color": "#FFFFFF",  # White legend labels
    },
    "ColorBar": {
        "background_fill_color": "#424242",
        "title_text_color": "#FFFFFF",
        "major_label_text_color": "#FFFFFF",
        "title_text_font_size": "16pt",
    },
    "Text": {
        "text_color": "#FFFFFF",
    },
}
lightprops = {
    "Plot": {
        "background_fill_color": "#FAFAFA",  # grey-lighten-3 (paper_bgcolor)
        "border_fill_color": "#EEEEEE",
        "outline_line_color": "#BDBDBD",  # lighten-1
    },
    "Axis": {
        "major_tick_line_color":
        "#212121",  # grey-darken-4 (dark ticks for contrast)
        "minor_tick_line_color": "#616161",  # grey-darken-2
        "axis_line_color": "#616161",
        "major_label_text_color": "#212121",  # grey-darken-4
        "major_label_text_font_size": "11pt",
        "axis_label_text_color": "#212121",  # grey-darken-4
        "axis_label_text_font_size": "16pt",
    },
    "Grid": {
        "grid_line_color": "#BDBDBD",  # grey-lighten-1 (x/y grid)
    },
    "Title": {
        "text_color": "#212121",  # grey-darken-4
        "text_font_size": "16pt",
    },
    "Legend": {
        "background_fill_color": "#EEEEEE",
        "label_text_color": "#212121",  # grey-darken-4
    },
    "ColorBar": {
        "background_fill_color": "#EEEEEE",
        "title_text_color": "#212121",
        "major_label_text_color": "#212121",
        "title_text_font_size": "16pt",
    },
    "Text": {
        "text_color": "#212121",
    },
}

DARKTHEME = Theme(json={"attrs": darkprops})
LIGHTTHEME = Theme(json={"attrs": lightprops})
