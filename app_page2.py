# app_page2.py
from reactpy import component, html, hooks
import httpx

from app_styles import box_style


def _bubble_style(sender: str):
    if sender == "user":
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
        "position": "relative",
    }


@component
def Page2():
    messages, set_messages = hooks.use_state(
        [
            {
                "sender": "ai",
                "text": "Hi, I’m your notes chatbot. Ask me anything about your documents or ideas.",
                "citations": [],
            }
        ]
    )
    input_text, set_input_text = hooks.use_state("")
    is_sending, set_is_sending = hooks.use_state(False)
    error_text, set_error_text = hooks.use_state("")
    # For citations popup
    show_citations, set_show_citations = hooks.use_state(False)
    current_citations, set_current_citations = hooks.use_state([])

    async def on_input(event):
        set_input_text(event["target"]["value"])

    async def on_keydown(event):
        # ReactPy keyboard events use 'shift_key' not 'shiftKey'
        if event.get("key") == "Enter" and not event.get("shift_key"):
            # prevent newline and send the message
            await send_message(event)
            
    def open_citations(cites):
        set_current_citations(cites or [])
        set_show_citations(True)

    async def send_message(event=None):
        nonlocal messages, input_text
        text = input_text.strip()
        if not text or is_sending:
            return

        # append user message locally
        new_messages = messages + [{"sender": "user", "text": text, "citations": []}]
        set_messages(new_messages)
        # clear input immediately
        set_input_text("")
        set_error_text("")
        set_is_sending(True)

        try:
            timeout = httpx.Timeout(60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "http://127.0.0.1:5000/api/chat",
                    json={"message": text},
                )
                data = resp.json()
                if resp.status_code != 200 or "error" in data:
                    set_error_text(str(data.get("error", "Chat error")))
                    return
                reply = data.get("reply", "")
                citations = data.get("citations", [])
        except Exception as e:
            set_error_text(f"Chat request failed: {e}")
            return
        finally:
            set_is_sending(False)

        # append assistant reply with citations
        set_messages(
            new_messages
            + [
                {
                    "sender": "ai",
                    "text": reply,
                    "citations": citations,
                }
            ]
        )

    # Citations modal
    citations_modal = (
        html.div(
            {
                "style": {
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "width": "100vw",
                    "height": "100vh",
                    "background_color": "rgba(0,0,0,0.4)",
                    "display": "flex",
                    "justify_content": "center",
                    "align_items": "center",
                    "z_index": "2000",
                }
            },
            html.div(
                {
                    "style": {
                        "background_color": "#ffffff",
                        "padding": "16px",
                        "border_radius": "8px",
                        "max_width": "600px",
                        "width": "90%",
                        "max_height": "70vh",
                        "overflow_y": "auto",
                        "box_shadow": "0 2px 8px rgba(0,0,0,0.25)",
                        "font_size": "14px",
                    }
                },
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "justify_content": "space_between",
                            "align_items": "center",
                            "margin_bottom": "8px",
                        }
                    },
                    html.b("Sources"),
                    html.button(
                        {
                            "on_click": lambda event: set_show_citations(False),
                            "style": {
                                "border": "none",
                                "background": "none",
                                "cursor": "pointer",
                                "font_size": "16px",
                            },
                        },
                        "×",
                    ),
                ),
                (
                    html.ul(
                        [
                            html.li(
                                html.a(
                                    {"href": url, "target": "_blank", "rel": "noreferrer"},
                                    url,
                                )
                            )
                            for url in current_citations
                            if url
                        ]
                    )
                    if current_citations
                    else html.p("No sources available for this message.")
                ),
            ),
        )
        if show_citations
        else None
    )

    return html.div(
        {
            "style": {
                **box_style,
                "display": "flex",
                "flex_direction": "column",
            }
        },
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
        html.div(
            {
                "style": {
                    "border": "1px solid #dadce0",
                    "border_radius": "16px",
                    "padding": "16px",
                    "flex": "1",
                    "min_height": "420px",
                    "overflow_y": "auto",
                    "background_color": "#f9fafb",
                    "display": "flex",
                    "flex_direction": "column",
                    "gap": "12px",
                    "margin_bottom": "12px",
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
                        # Bubble content + optional info icon for AI
                        html.div(
                            {
                                "style": {
                                    "display": "flex",
                                    "align_items": "flex-start",
                                    "gap": "6px",
                                }
                            },
                            html.div({"style": {"flex": "1"}}, msg["text"]),
                            (
                                html.button(
                                    {
                                        "on_click": lambda event, cites=msg.get(
                                            "citations", []
                                        ): open_citations(cites),
                                        "style": {
                                            "border": "none",
                                            "background": "none",
                                            "cursor": "pointer",
                                            "font_size": "12px",
                                            "color": "#6b7280",
                                        },
                                    },
                                    "i",
                                )
                                if msg["sender"] == "ai"
                                and msg.get("citations")
                                else None
                            ),
                        ),
                    ),
                )
                for msg in messages
            ],
        ),
        html.div(
            {
                "style": {
                    "color": "#b91c1c",
                    "font_size": "13px",
                    "min_height": "16px",
                    "margin_bottom": "4px",
                }
            },
            error_text or "",
        ),
        html.div(
            {
                "style": {
                    "display": "flex",
                    "align_items": "center",
                    "gap": "8px",
                }
            },
            html.textarea(
                {
                    "value": input_text,
                    "on_input": on_input,
                    "on_keydown": on_keydown,
                    "rows": 2,
                    "placeholder": "Type a message and press Enter...",
                    "style": {
                        "flex": "1",
                        "resize": "none",
                        "border_radius": "12px",
                        "border": "1px solid #dadce0",
                        "padding": "8px 10px",
                        "font_size": "14px",
                    },
                }
            ),
            html.button(
                {
                    "on_click": send_message,
                    "disabled": is_sending,
                    "style": {
                        "padding": "8px 14px",
                        "border_radius": "999px",
                        "border": "none",
                        "background_color": "#2563eb",
                        "color": "white",
                        "cursor": "pointer",
                        "font_size": "14px",
                        "min_width": "72px",
                    },
                },
                "Send" if not is_sending else "Sending...",
            ),
        ),
        citations_modal,
    )
