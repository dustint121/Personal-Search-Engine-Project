# app_front.py
from reactpy import component, html, hooks
from reactpy.backend.flask import configure
import httpx

from app_backend import app
from app_styles import (
    page_style,
    nav_container_style,
    nav_tab_style,
    box_style,
    search_input_style,
    results_container_style,
    result_title_style,
    result_url_style,
)

@component
def RootApp():
    # "page1" = search page, "page2" = work-in-progress
    current_page, set_current_page = hooks.use_state("page1")

    query, set_query = hooks.use_state("")
    results, set_results = hooks.use_state([])
    is_loading, set_is_loading = hooks.use_state(False)

    # Track selected document IDs (strings)
    selected_ids, set_selected_ids = hooks.use_state(set())
    show_modal, set_show_modal = hooks.use_state(False)

    # Perplexity summary state
    summary_loading, set_summary_loading = hooks.use_state(False)
    summary_text, set_summary_text = hooks.use_state("")
    summary_error, set_summary_error = hooks.use_state("")

    # New: whether to use local files vs Graph
    use_local_source, set_use_local_source = hooks.use_state(False)

    async def submit_search():
        q_value = query.strip()
        # Clear previous selection and summary on new search
        set_selected_ids(set())
        set_summary_text("")
        set_summary_error("")

        if not q_value:
            set_results([])
            set_is_loading(False)
            return

        set_is_loading(True)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://127.0.0.1:5000/api/search",
                    params={"q": q_value},
                )
                data = resp.json()
                if isinstance(data, dict) and "error" in data:
                    set_results([])
                else:
                    set_results(data)
        finally:
            set_is_loading(False)

    async def on_input(event):
        set_query(event["target"]["value"])

    async def on_keydown(event):
        if event.get("key") == "Enter":
            await submit_search()

    def switch_page(page_name: str):
        set_current_page(page_name)
        set_show_modal(False)

    def get_doc_id(doc: dict) -> str:
        # Prefer Graph "id", else fallback to URL, then title
        return str(doc.get("id") or doc.get("url") or doc.get("title"))

    def toggle_selected(doc_id: str):
        def updater(prev_ids):
            new_ids = set(prev_ids)
            if doc_id in new_ids:
                new_ids.remove(doc_id)
            else:
                new_ids.add(doc_id)
            return new_ids
        set_selected_ids(updater)

    def get_selected_docs():
        return [r for r in results if get_doc_id(r) in selected_ids]

    # Result count
    result_count_text = ""
    if not is_loading and query:
        count = len(results)
        if count == 0:
            result_count_text = "0 results found"
        elif count == 1:
            result_count_text = "1 result found"
        else:
            result_count_text = f"{count} results found"

    # Page 1: search UI
    page1_content = html.div(
        {"style": box_style},
        html.h1(
            {"style": {"margin_bottom": "16px"}},
            "Personal OneDrive Search Engine",
        ),
        html.div(
            {
                "style": {
                    "display": "flex",
                    "justify_content": "center",
                    "align_items": "center",
                }
            },
            html.input(
                {
                    "type": "text",
                    "value": query,
                    "placeholder": "Search your OneDrive notes... (press Enter)",
                    "on_input": on_input,
                    "on_keydown": on_keydown,
                    "style": {
                        **search_input_style,
                        "max_width": "600px",
                    },
                }
            ),
        ),
        html.div(
            {
                "style": {
                    "margin_top": "8px",
                    "font_size": "13px",
                    "color": "#5f6368",
                }
            },
            result_count_text,
        )
        if result_count_text
        else None,
        html.div(
            {"style": results_container_style},
            (
                html.p("Processing query...")
                if is_loading
                else (
                    html.ul(
                        [
                            html.li(
                                {
                                    "style": {
                                        "list_style_type": "none",
                                        "margin_bottom": "8px",
                                    }
                                },
                                html.label(
                                    {
                                        "style": {
                                            "display": "flex",
                                            "align_items": "flex-start",
                                            "gap": "8px",
                                        }
                                    },
                                    html.input(
                                        {
                                            "type": "checkbox",
                                            "checked": get_doc_id(r) in selected_ids,
                                            "on_change": (
                                                lambda event, doc_id=get_doc_id(r):
                                                toggle_selected(doc_id)
                                            ),
                                        }
                                    ),
                                    html.div(
                                        html.a(
                                            {
                                                "href": r["url"],
                                                "style": result_title_style,
                                            },
                                            r["title"],
                                        ),
                                        html.div(
                                            {"style": result_url_style},
                                            r["url"],
                                        ),
                                    ),
                                ),
                            )
                            for r in results
                        ]
                    )
                    if results
                    else (
                        html.p("No results.")
                        if query and not results
                        else None
                    )
                )
            ),
        ),
    )

    # Page 2: Work in Progress
    page2_content = html.div(
        {"style": box_style},
        html.h1({"style": {"margin_bottom": "16px"}}, "Work in Progress"),
        html.p(
            "This page is under construction. Future features for your OneDrive search engine will appear here."
        ),
    )

    main_content = page1_content if current_page == "page1" else page2_content

    # Bottom-right arrow button (opens modal)
    arrow_button = html.button(
        {
            "style": {
                "position": "fixed",
                "right": "24px",
                "bottom": "24px",
                "width": "52px",
                "height": "52px",
                "border_radius": "26px",
                "border": "none",
                "background_color": "#1a73e8",
                "color": "white",
                "font_size": "24px",
                "cursor": "pointer",
                "box_shadow": "0 2px 6px rgba(0,0,0,0.3)",
            },
            "on_click": lambda event: set_show_modal(True),
        },
        "→",
    ) if current_page == "page1" else None

    # Summarize button handler inside modal
    async def on_summarize_click(event):
        docs = get_selected_docs()
        ids = [get_doc_id(d) for d in docs]
        if not ids:
            set_summary_error("No documents selected to summarize.")
            return

        set_summary_loading(True)
        set_summary_error("")
        set_summary_text("")
        try:
            timeout = httpx.Timeout(120.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "http://127.0.0.1:5000/api/summarize",
                    json={
                        "ids": ids,
                        "source": "local" if use_local_source else "cloud",
                    },
                )
                data = resp.json()
                if resp.status_code != 200 or "error" in data:
                    set_summary_error(str(data.get("error", "Unknown error")))
                else:
                    set_summary_text(data.get("summary", ""))
        except httpx.ReadTimeout:
            set_summary_error(
                "Summarization request timed out. Please try again or select fewer documents."
            )
        except Exception as e:
            set_summary_error(f"Unexpected error: {e}")
        finally:
            set_summary_loading(False)

    # Modal overlay listing selected documents and summary
    selected_docs = get_selected_docs()
    source_label = (
        "Using local note_files for document content."
        if use_local_source
        else "Using cloud (Graph API) for document content."
    )

    modal = (
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
                    "z_index": "1000",
                }
            },
            html.div(
                {
                    "style": {
                        "background_color": "#ffffff",
                        "padding": "20px",
                        "border_radius": "8px",
                        "max_width": "600px",
                        "width": "90%",
                        "max_height": "80vh",
                        "overflow_y": "auto",
                        "box_shadow": "0 2px 8px rgba(0,0,0,0.3)",
                    }
                },
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "justify_content": "space_between",
                            "align_items": "center",
                            "margin_bottom": "12px",
                        }
                    },
                    html.h3("Selected Documents"),
                    html.button(
                        {
                            "on_click": lambda event: set_show_modal(False),
                            "style": {
                                "margin_left": "auto",
                                "border": "none",
                                "background": "none",
                                "font_size": "18px",
                                "cursor": "pointer",
                            },
                        },
                        "X",
                    ),
                ),
                # List of selected doc titles
                (
                    html.ul(
                        [
                            html.li(doc.get("title", "(no name)"))
                            for doc in selected_docs
                        ]
                    )
                    if selected_docs
                    else html.p("No documents selected.")
                ),
                # Source toggle checkbox
                html.div(
                    {
                        "style": {
                            "margin_top": "12px",
                            "display": "flex",
                            "align_items": "center",
                            "gap": "6px",
                        }
                    },
                    html.input(
                        {
                            "type": "checkbox",
                            "checked": use_local_source,
                            "on_change": (
                                lambda event: set_use_local_source(
                                    not use_local_source
                                )
                            ),
                        }
                    ),
                    html.span("Use local note_files instead of cloud (Graph)"),
                ),
                # Source status line
                html.div(
                    {
                        "style": {
                            "margin_top": "8px",
                            "font_size": "13px",
                            "color": "#5f6368",
                        }
                    },
                    source_label,
                ),
                # Summarize button
                html.div(
                    {
                        "style": {
                            "margin_top": "16px",
                            "display": "flex",
                            "justify_content": "flex-end",
                        }
                    },
                    html.button(
                        {
                            "on_click": on_summarize_click,
                            "style": {
                                "padding": "8px 14px",
                                "border_radius": "4px",
                                "border": "none",
                                "background_color": "#1a73e8",
                                "color": "white",
                                "cursor": "pointer",
                                "font_size": "14px",
                            },
                            "disabled": summary_loading,
                        },
                        "Summarize",
                    ),
                ),
                # Summary status / result
                html.div(
                    {
                        "style": {
                            "margin_top": "16px",
                            "font_size": "14px",
                            "white_space": "pre-wrap",
                        }
                    },
                    (
                        # Your requested message before summarization
                        (
                            f"{source_label} Summarizing selected documents..."
                            if summary_loading
                            else (
                                summary_error
                                if summary_error
                                else summary_text
                            )
                        )
                    ),
                ),
            ),
        )
        if show_modal and current_page == "page1"
        else None
    )

    return html.div(
        {"style": page_style},
        html.div(
            {"style": nav_container_style},
            html.div(
                {
                    "style": nav_tab_style(current_page == "page1"),
                    "on_click": lambda event: switch_page("page1"),
                },
                "Page 1",
            ),
            html.div(
                {
                    "style": nav_tab_style(current_page == "page2"),
                    "on_click": lambda event: switch_page("page2"),
                },
                "Page 2",
            ),
        ),
        main_content,
        arrow_button,
        modal,
    )

configure(app, RootApp)

if __name__ == "__main__":
    app.run(debug=True)
