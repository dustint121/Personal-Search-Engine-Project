# styles.py

page_style = {
    "min_height": "100vh",
    "display": "flex",
    "justify_content": "center",
    "align_items": "center",
    "background_color": "#f8f9fa",
    "font_family": "Arial, sans-serif",
    "position": "relative",
}

nav_container_style = {
    "position": "absolute",
    "top": "16px",
    "left": "16px",
    "display": "flex",
    "border": "1px solid #dadce0",
    "border_radius": "8px",
    "overflow": "hidden",
    "background_color": "#ffffff",
    "box_shadow": "0 1px 4px rgba(0,0,0,0.1)",
}

def nav_tab_style(active: bool):
    base = {
        "padding": "8px 16px",
        "cursor": "pointer",
        "font_size": "14px",
        "border_right": "1px solid #dadce0",
    }
    if active:
        base["background_color"] = "#1a73e8"
        base["color"] = "#ffffff"
        base["font_weight"] = "bold"
    else:
        base["background_color"] = "#ffffff"
        base["color"] = "#5f6368"
    return base

box_style = {
    "width": "100%",
    "max_width": "600px",
    "text_align": "center",
}

search_input_style = {
    "width": "100%",
    "padding": "12px 16px",
    "border_radius": "24px",
    "border": "1px solid #dfe1e5",
    "box_shadow": "0 1px 6px rgba(32,33,36,.28)",
    "font_size": "16px",
    "outline": "none",
}

results_container_style = {
    "margin_top": "24px",
    "text_align": "left",
}

result_title_style = {
    "font_size": "16px",
    "color": "#1a0dab",
    "text_decoration": "none",
}

result_url_style = {
    "font_size": "12px",
    "color": "#006621",
}
