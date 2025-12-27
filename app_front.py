# app_front.py
from reactpy import component, html, hooks
from reactpy.backend.flask import configure

from app_backend import app
from app_styles import page_style, nav_container_style, nav_tab_style
from app_page1 import Page1
from app_page2 import Page2


@component
def RootApp():
    # "page1" = search page, "page2" = work-in-progress
    current_page, set_current_page = hooks.use_state("page1")

    def switch_page(page_name: str):
        set_current_page(page_name)

    main_content = Page1() if current_page == "page1" else Page2()

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
    )


configure(app, RootApp)

if __name__ == "__main__":
    app.run(debug=True)
