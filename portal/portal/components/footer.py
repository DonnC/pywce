import reflex as rx


def _social_link(icon: str, href: str) -> rx.Component:
    return rx.link(rx.icon(icon), href=href)


def _socials() -> rx.Component:
    return rx.flex(
        _social_link("github", "https://github.com/DonnC"),
        _social_link("linkedin", "https://www.linkedin.com/in/donchinhuru"),
        _social_link("twitter", "https://x.com/donix_22"),
        spacing="3",
        justify_content=["center", "center", "end"],
        width="100%",
    )


def footer() -> rx.Component:
    return rx.el.footer(
        rx.vstack(
            rx.divider(),
            rx.flex(
                rx.hstack(
                    rx.text(
                        "©2025 DonnC Lab",
                        size="3",
                        white_space="nowrap",
                        weight="medium",
                    ),
                    spacing="2",
                    align="center",
                    justify_content=[
                        "center",
                        "center",
                        "start",
                    ],
                    width="100%",
                ),
                _socials(),
                spacing="4",
                flex_direction=["column", "column", "row"],
                width="100%",
            ),
            spacing="5",
            width="100%",
        ),
        width="100%",
        class_name="px-4"
    )
