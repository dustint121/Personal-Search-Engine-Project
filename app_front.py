# ui.py
from reactpy import component, html, hooks
from reactpy.backend.flask import configure
import httpx

from app_backend import app  # import the Flask app
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
def SearchApp():
    current_page, set_current_page = hooks.use_state("page1")
    query, set_query = hooks.use_state("")
    results, set_results = hooks.use_state([])

    async def on_input(event):
        q_value = event["target"]["value"]
        set_query(q_value)
        if not q_value:
            set_results([])
            return

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://127.0.0.1:5000/api/search",
                params={"q": q_value},
            )
            set_results(resp.json())

    def switch_page(page_name: str):
        set_current_page(page_name)

    # Page 1 content: search engine
    page1_content = html.div(
        {"style": box_style},
        html.h1(
            {"style": {"margin_bottom": "24px"}},
            "Personal OneDrive Search Engine",
        ),
        html.input(
            {
                "type": "text",
                "value": query,
                "placeholder": "Search your OneDrive notes...",
                "on_input": on_input,
                "style": search_input_style,
            }
        ),
        html.div(
            {"style": results_container_style},
            (
                html.ul(
                    [
                        html.li(
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
                            )
                        )
                        for r in results
                    ]
                )
                if results
                else (html.p("No results.") if query else None)
            ),
        ),
    )

    # Page 2 content: Work in Progress
    page2_content = html.div(
        {"style": box_style},
        html.h1({"style": {"margin_bottom": "16px"}}, "Work in Progress"),
        html.p(
            "This page is under construction. Future features for your OneDrive search engine will appear here."
        ),
    )

    main_content = page1_content if current_page == "page1" else page2_content

    return html.div(
        {"style": page_style},
        # Top-left page switcher
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
        # Centered content
        main_content,
    )

# Mount ReactPy UI onto the existing Flask app
configure(app, SearchApp)

if __name__ == "__main__":
    app.run(debug=True)
