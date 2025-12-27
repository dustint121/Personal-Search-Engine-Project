# app_page2.py
from reactpy import component, html
from app_styles import box_style

STATIC_MESSAGES = [
    {"sender": "user", "text": "who are you"},
    {
        "sender": "ai",
        "text": (
            "I’m Copilot — your AI companion built by Microsoft. I’m here to help you think, create, "
            "debug, research, plan, explore ideas, or just talk things through.\n\n"
            "What makes me different is that I’m designed to be more of a partner in thought, "
            "especially for technical topics like machine learning.\n\n"
            "If you want, I can also tell you what I’m especially good at or how I can be most useful to you."
        ),
    },
    {
        "sender": "user",
        "text": "testing the Copilot chat box size: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    },
    {
        "sender": "ai",
        "text": (
            "Looks like the chat box handled your stress-test just fine — long strings and line breaks "
            "don’t faze it."
        ),
    },
]


def _bubble_style(sender: str):
    if sender == "user":
        # compact, right-aligned blue bubble
        return {
            "display": "inline-block",
            "max_width": "70%",
            "padding": "8px 12px",
            "border_radius": "16px",
            "border_top_right_radius": "4px",
            "background_color": "#2563eb",
            "color": "#ffffff",
            "font_size": "14px",
            "line_height": "1.4",
            "white_space": "pre-wrap",
        }
    # AI: full-width, light background
    return {
        "width": "100%",
        "padding": "12px 16px",
        "border_radius": "16px",
        "border_top_left_radius": "4px",
        "background_color": "#ffffff",
        "color": "#111827",
        "font_size": "14px",
        "line_height": "1.5",
        "white_space": "pre-wrap",
        "box_sizing": "border-box",
        "box_shadow": "0 1px 2px rgba(15,23,42,0.08)",
    }


@component
def Page2():
    return html.div(
        {
            "style": {
                **box_style,
                "display": "flex",
                "flex_direction": "column",
            }
        },
        # Title centered at top of Page 2
        html.div(
            {
                "style": {
                    "width": "100%",
                    "text_align": "center",
                    "margin_bottom": "12px",
                }
            },
            html.h1(
                {
                    "style": {
                        "margin": 0,
                        "font_size": "20px",
                        "font_weight": "500",
                    }
                },
                "Chat Prototype",
            ),
        ),
        # Light chat container, no black background
        html.div(
            {
                "style": {
                    "border": "1px solid #dadce0",
                    "border_radius": "16px",
                    "padding": "16px",
                    "flex": "1",
                    "min_height": "520px",
                    "overflow_y": "auto",
                    "background_color": "#f9fafb",  # light gray
                    "display": "flex",
                    "flex_direction": "column",
                    "gap": "12px",
                }
            },
            [
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "justify_content": (
                                "flex_end" if msg["sender"] == "user" else "flex_start"
                            ),
                        }
                    },
                    html.div(
                        {"style": _bubble_style(msg["sender"])},
                        msg["text"],
                    ),
                )
                for msg in STATIC_MESSAGES
            ],
        ),
    )
