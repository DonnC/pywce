import reflex as rx


class AppConfig(rx.Config):
    pass


config = AppConfig(
    app_name="portal",
    db_url="sqlite:///pywce_support.db",
    env=rx.Env.DEV,
    tailwind={
        "theme": {
            "extend": {},
        },
        "plugins": ["@tailwindcss/typography"],
    },
)
