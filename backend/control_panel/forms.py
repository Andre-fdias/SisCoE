from django import forms
from .models import SystemSettings


class SettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Popula o formulário dinamicamente com as configurações do banco de dados
        settings = SystemSettings.objects.all()
        for setting in settings:
            field_key = setting.key
            field_value = setting.value
            field_description = setting.description

            # Tenta inferir o tipo de campo
            if field_value.lower() in ["true", "false"]:
                self.fields[field_key] = forms.BooleanField(
                    label=field_key.replace("_", " ").capitalize(),
                    required=False,
                    initial=field_value.lower() == "true",
                    help_text=field_description,
                )
            elif field_value.isdigit():
                self.fields[field_key] = forms.IntegerField(
                    label=field_key.replace("_", " ").capitalize(),
                    initial=int(field_value),
                    help_text=field_description,
                )
            else:
                self.fields[field_key] = forms.CharField(
                    label=field_key.replace("_", " ").capitalize(),
                    initial=field_value,
                    widget=(
                        forms.Textarea(attrs={"rows": 2})
                        if "\n" in field_value
                        else forms.TextInput
                    ),
                    help_text=field_description,
                )

    def save(self):
        for key, value in self.cleaned_data.items():
            # Converte booleano de volta para string para salvar no banco
            if isinstance(value, bool):
                value = "True" if value else "False"

            SystemSettings.objects.update_or_create(
                key=key, defaults={"value": str(value)}
            )
