# Modelos do Aplicativo Core

## `Profile`

O modelo `Profile` estende o modelo `User` do Django, adicionando informações adicionais como posto/graduação, CPF, tipo (administrativo/operacional) e imagem de perfil.

```python
from backend.accounts.models import User
from django.db import models
from backend.efetivo.models import Cadastro

class Profile(models.Model):
    # ... campos do modelo ...

    def __str__(self):
        return self.full_name

    @property
    def grad(self):
        # ... lógica para exibir posto/graduação com formatação HTML ...
        pass