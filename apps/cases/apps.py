from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cases"
    label = "cases"

    def ready(self) -> None:
        from services import fusion_model
        fusion_model._load_artifacts()
