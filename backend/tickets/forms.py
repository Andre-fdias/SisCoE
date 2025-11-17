from django import forms
from .models import Chamado, Categoria, Comentario
from backend.accounts.models import User
from backend.efetivo.models import Cadastro


class ChamadoForm(forms.ModelForm):
    anexos = forms.FileField(
        required=False,
        label="Anexos",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400",
            }
        ),
    )

    categoria_principal = forms.ChoiceField(
        choices=[("", "Selecione uma categoria")]
        + list(Categoria.TIPO_PROBLEMA_CHOICES),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200",
                "id": "id_categoria_principal",
            }
        ),
    )
    subcategoria = forms.ChoiceField(
        choices=[("", "Selecione primeiro uma categoria")],
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200",
                "id": "id_subcategoria",
            }
        ),
    )

    class Meta:
        model = Chamado
        fields = ["solicitante_cpf", "assunto", "descricao"]
        widgets = {
            "solicitante_cpf": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400 cpf-mask",
                    "placeholder": "000.000.000-00",
                    "id": "cpf-input",
                }
            ),
            "assunto": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400",
                    "placeholder": "Breve descrição do problema",
                    "id": "assunto-input",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-400",
                    "rows": 5,
                    "placeholder": "Descreva o problema em detalhes...",
                    "id": "descricao-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Popula dinamicamente as subcategorias se o formulário for submetido
        if self.is_bound and self.data.get("categoria_principal"):
            cat_principal = self.data.get("categoria_principal")
            sub_categorias = Categoria.objects.filter(categoria=cat_principal)
            sub_choices = [
                (sub.subcategoria, sub.get_subcategoria_display())
                for sub in sub_categorias
            ]
            self.fields["subcategoria"].choices = [
                ("", "Selecione uma subcategoria")
            ] + sub_choices

    def clean(self):
        cleaned_data = super().clean()
        cat_principal = cleaned_data.get("categoria_principal")
        sub_cat = cleaned_data.get("subcategoria")

        if cat_principal and sub_cat:
            try:
                categoria_obj = Categoria.objects.get(
                    categoria=cat_principal, subcategoria=sub_cat
                )
                self.cleaned_data["categoria"] = categoria_obj
            except Categoria.DoesNotExist:
                raise forms.ValidationError(
                    "A combinação de categoria e subcategoria selecionada é inválida."
                )
        else:
            if not self.errors:
                raise forms.ValidationError(
                    "Categoria e Subcategoria são obrigatórias."
                )

        # Validação de anexos
        anexos = self.files.getlist("anexos")
        if len(anexos) > 10:
            self.add_error("anexos", "Máximo de 10 anexos permitidos.")

        total_size = sum([f.size for f in anexos])
        if total_size > 2 * 1024 * 1024:
            self.add_error("anexos", "Tamanho total dos anexos não pode exceder 2MB.")

        return cleaned_data

    def clean_solicitante_cpf(self):
        cpf = self.cleaned_data.get("solicitante_cpf")
        if cpf:
            if len(cpf) != 14:
                raise forms.ValidationError(
                    "Formato de CPF inválido. Use XXX.XXX.XXX-XX."
                )
            try:
                Cadastro.objects.get(cpf=cpf)
            except Cadastro.DoesNotExist:
                raise forms.ValidationError("Militar não encontrado com este CPF.")
        return cpf


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["texto", "privado"]
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Adicione seu comentário...",
                }
            ),
            "privado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "texto": "Novo Comentário",
            "privado": "Marcar como comentário privado (visível apenas para a equipe)",
        }


class UpdateStatusForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}


class AssignTecnicoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["tecnico_responsavel"]
        widgets = {"tecnico_responsavel": forms.Select(attrs={"class": "form-select"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CORREÇÃO: Use is_admin em vez de is_staff
        self.fields["tecnico_responsavel"].queryset = User.objects.filter(is_admin=True)
        self.fields["tecnico_responsavel"].label = "Atribuir Técnico"
