import reflex as rx

from ..state import WebhookState


def _webhook_stats() -> rx.Component:
    """Display webhook statistics."""
    return rx.vstack(
        rx.heading("Webhook Statistics", font_size="1.5em"),
        rx.text(f"Total Webhooks: {WebhookState.webhook_count}"),
        rx.text(f"Last Webhook: {WebhookState.last_webhook_time}"),
        spacing="4",
    )


def webhook_stat_card() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Webhook Dashboard", font_size="2em"),
            _webhook_stats(),
            width="100%",
            max_width="800px",
            spacing="2",
            padding="2em",
        )
    )
