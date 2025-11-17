# backend/cursos/resources.py

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Medalha, Cadastro, Curso  # Importe o modelo Curso


class CadastroForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        """
        Custom clean method to handle 'RE' for Cadastro.
        If the value is a number, assume it's an ID.
        Otherwise, try to find by 're'.
        """
        if value:
            try:
                # Try to convert to int, implying it's a primary key (ID)
                cadastro_id = int(value)
                return self.model.objects.get(pk=cadastro_id)
            except (ValueError, self.model.DoesNotExist):
                # If not an int or ID not found, try to find by 're'
                try:
                    return self.model.objects.get(re=value)
                except self.model.DoesNotExist:
                    raise ValueError(f"Militar com RE ou ID '{value}' não encontrado.")
        return None


class MedalhaResource(resources.ModelResource):
    # Campo para o RE do Cadastro, usando o widget customizado
    cadastro_re = fields.Field(
        column_name="RE_Militar",
        attribute="cadastro",
        widget=CadastroForeignKeyWidget(Cadastro, "re"),  # Mapeia para o RE do Cadastro
    )

    # Campo para o nome do Militar (apenas exportação, não importação)
    nome_militar = fields.Field(
        column_name="Nome_Militar",
        attribute="cadastro__nome",  # Acessa o nome do objeto Cadastro relacionado
        readonly=True,  # Este campo é apenas para exportação, não para importação
    )

    class Meta:
        model = Medalha
        # Defina os campos a serem exportados/importados
        fields = (
            "id",
            "cadastro_re",  # Use o campo customizado para RE
            "nome_militar",  # Apenas para exportação
            "honraria",
            "bol_g_pm_lp",
            "data_publicacao_lp",
            "observacoes",
        )
        # Campos que não serão importados ou exportados
        exclude = (
            "usuario_cadastro",
            "data_cadastro",
            "usuario_alteracao",
            "data_alteracao",
            "cadastro",
        )
        # O campo 'cadastro' original é excluído pois estamos usando 'cadastro_re'

        # Campos necessários para importação
        import_id_fields = (
            "id",
        )  # Use 'id' para atualizar registros existentes, se aplicável

    def before_import_row(self, row, **kwargs):
        """
        Antes de importar uma linha, você pode manipular os dados.
        Aqui, garantimos que o 'cadastro' seja populado corretamente
        se 'RE_Militar' estiver presente.
        """
        re_militar = row.get("RE_Militar")
        if re_militar:
            try:
                cadastro = Cadastro.objects.get(re=re_militar)
                # O widget `CadastroForeignKeyWidget` já lida com a atribuição correta para `cadastro`
                # Então, não precisamos setar `row['cadastro']` aqui se o widget estiver fazendo seu trabalho
                # Mas é um bom lugar para debug ou lógica adicional se o widget não for suficiente.
                pass
            except Cadastro.DoesNotExist:
                raise ValueError(
                    f"Militar com RE '{re_militar}' não encontrado na linha: {row}"
                )

    def get_export_headers(self, selected_fields=None):
        """
        Define a ordem e o nome das colunas no arquivo CSV exportado.
        """
        headers = []
        for field_name in self.fields.keys():
            if (
                field_name in self.Meta.fields
            ):  # Apenas campos que estão na lista de exportação
                field = self.fields[field_name]
                headers.append(field.column_name)
        return headers


# --- Novo Resource para o modelo Curso ---


class CursoResource(resources.ModelResource):
    # Campo para o RE do Cadastro, usando o widget customizado
    cadastro_re = fields.Field(
        column_name="RE_Militar",
        attribute="cadastro",
        widget=CadastroForeignKeyWidget(Cadastro, "re"),  # Mapeia para o RE do Cadastro
    )

    # Campo para o nome do Militar (apenas exportação, não importação)
    nome_militar = fields.Field(
        column_name="Nome_Militar",
        attribute="cadastro__nome",  # Acessa o nome do objeto Cadastro relacionado
        readonly=True,  # Este campo é apenas para exportação, não para importação
    )

    class Meta:
        model = Curso
        # Defina os campos a serem exportados/importados
        fields = (
            "id",
            "cadastro_re",  # Use o campo customizado para RE
            "nome_militar",  # Apenas para exportação
            "curso",
            "outro_curso",
            "bol_publicacao",
            "data_publicacao",
            "observacoes",
        )
        # Campos que não serão importados ou exportados
        exclude = (
            "usuario_cadastro",
            "data_cadastro",
            "usuario_alteracao",
            "data_alteracao",
            "cadastro",
        )

        # Campos necessários para importação
        import_id_fields = (
            "id",
        )  # Use 'id' para atualizar registros existentes, se aplicável

    def before_import_row(self, row, **kwargs):
        """
        Antes de importar uma linha, você pode manipular os dados para o Curso.
        """
        re_militar = row.get("RE_Militar")
        if re_militar:
            try:
                cadastro = Cadastro.objects.get(re=re_militar)
                # O widget `CadastroForeignKeyWidget` já lida com a atribuição correta para `cadastro`
                pass
            except Cadastro.DoesNotExist:
                raise ValueError(
                    f"Militar com RE '{re_militar}' não encontrado na linha: {row}"
                )

    def get_export_headers(self, selected_fields=None):
        """
        Define a ordem e o nome das colunas no arquivo CSV exportado para Curso.
        """
        headers = []
        for field_name in self.fields.keys():
            if (
                field_name in self.Meta.fields
            ):  # Apenas campos que estão na lista de exportação
                field = self.fields[field_name]
                headers.append(field.column_name)
        return headers
