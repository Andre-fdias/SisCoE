from datetime import date, datetime

# Remova: from django.contrib.auth import get_user_model
from django.conf import (
    settings,
)  # Adicione esta importação para acessar AUTH_USER_MODEL
from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils.safestring import mark_safe
from django.db.models.signals import post_save
from django.dispatch import receiver
import locale
from django.utils import timezone

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "C.UTF-8")  # Fallback para locale neutra
    # Ou alternativamente: pass (não altera a locale)

# responsavel pelo cadastro básico de dados de militares


class Cadastro(models.Model):
    genero_choices = (("", " "), ("Masculino", "Masculino"), ("Feminino", "Feminino"))

    alteracao_choices = (
        ("", ""),
        ("Movimentação", "Movimentação"),
        ("Promoção", "Promoção"),
        ("Foto", "Foto"),
        ("Averbação", "Averbação"),
        ("Correção", "Correção"),
        ("Documento", "Documento"),
        ("Contato", "Contato"),
        ("Inclusão", "Inclusão"),
    )
    n_choices = [(i, f"{i:02d}") for i in range(1, 9)]

    id = models.AutoField(primary_key=True)
    re = models.CharField(max_length=6, blank=False, null=False, unique=True)
    dig = models.CharField(max_length=1, blank=False, null=False)
    nome = models.CharField(max_length=50, blank=False, null=False)
    nome_de_guerra = models.CharField(max_length=20, blank=False, null=False)
    genero = models.CharField(
        max_length=10, blank=False, null=False, choices=genero_choices
    )
    nasc = models.DateField(blank=False, null=False)
    matricula = models.DateField(blank=False, null=False)
    admissao = models.DateField(blank=False, null=False)
    previsao_de_inatividade = models.DateField(blank=False, null=False)
    cpf = models.CharField(max_length=14, blank=False, null=False, unique=True)
    rg = models.CharField(max_length=14, blank=False, null=False)
    tempo_para_averbar_inss = models.IntegerField(blank=False, null=False, default=1)
    tempo_para_averbar_militar = models.IntegerField(blank=False, null=False, default=1)
    email = models.EmailField(max_length=100, unique=True, blank=False, null=False)
    telefone = models.CharField(max_length=14, blank=False, null=False)
    alteracao = models.CharField(
        max_length=20, blank=False, null=False, choices=alteracao_choices
    )
    create_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cadastros",
        default=1,
    )

    def __str__(self):
        return f"{self.re} {self.dig} {self.nome_de_guerra}"

    @property
    def idade_detalhada(self):
        hoje = datetime.today()
        delta = relativedelta(hoje, self.nasc)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    def matricula_detalhada(self):
        hoje = datetime.today()
        delta = relativedelta(hoje, self.matricula)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    def admissao_detalhada(self):
        hoje = datetime.today()
        delta = relativedelta(hoje, self.admissao)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    def previsao_de_inatividade_detalhada(self):
        hoje = datetime.today()
        delta = relativedelta(self.previsao_de_inatividade, hoje)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    def previsao_de_inatividade_dias(self):
        hoje = datetime.today().date()
        delta = self.previsao_de_inatividade - hoje
        return delta.days

    def tempo_para_inatividade(self):
        hoje = datetime.now().date()
        diferenca = hoje - self.previsao_de_inatividade
        return diferenca.days

    @property
    def inativa_status(self):
        dias = self.previsao_de_inatividade_dias()
        if dias < 1:
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">Sim</span>'
            )
        if dias < 180:
            return mark_safe(
                '<span class="bg-yellow-500 text-white px-2 py-1 rounded">Falta menos de 06 meses</span>'
            )
        if dias < 367:
            return mark_safe(
                '<span class="bg-gray-500 text-white px-2 py-1 rounded">Falta menos de 1 ano</span>'
            )
        return mark_safe(
            '<span class="bg-red-500 text-white px-2 py-1 rounded">Não</span>'
        )

    @property
    def tempo_para_averbar_inss_inteiro(self):
        return self.tempo_para_averbar_inss

    @property
    def tempo_para_averbar_militar_inteiro(self):
        return self.tempo_para_averbar_militar

    @property
    def ultima_promocao(self):
        try:
            return self.promocoes.latest("data_alteracao")
        except Promocao.DoesNotExist:
            return None

    def categoria_ativa(self):
        return self.categorias_efetivo.filter(ativo=True).first()

    class Meta:
        ordering = ("re",)

    def get_search_result(self):
        return {
            "title": f"{self.nome_de_guerra} ({self.re}-{self.dig})",
            "fields": {
                "RE": f"{self.re}-{self.dig}",
                "Nome": self.nome,
                "CPF": self.cpf,
                "Email": self.email,
                "Telefone": self.telefone,
            },
        }


class CPF(models.Model):
    id = models.IntegerField(primary_key=True)
    cpf = models.CharField(max_length=14)
    re = models.CharField(max_length=6)


@receiver(post_save, sender=Cadastro)
def create_cpf_record(sender, instance, created, **kwargs):
    if created:
        CPF.objects.create(id=instance.id, cpf=instance.cpf, re=instance.re)


# responsavel pelo cadastro sa situação funcional de militares
class DetalhesSituacao(models.Model):

    situacao_choices = (
        ("", " "),
        ("Efetivo", "Efetivo"),
        ("Exonerado a Pedido", "Exonerado a Pedido"),
        ("Exonerado Ex-Ofício", "Exonerado Ex-Ofício"),
        ("Reserva a Pedido", "Reserva a Pedido"),
        ("Transferido", "Transferido"),
        ("Mov. Interna", "Mov. Interna"),
    )
    sgb_choices = (
        ("", " "),
        ("EM", " EM"),
        ("1ºSGB", "1ºSGB"),
        ("2ºSGB", "2ºSGB"),
        ("3ºSGB", "3ºSGB"),
        ("4ºSGB", "4ºSGB"),
        ("5ºSGB", "5ºSGB"),
    )

    op_adm_choices = (
        ("", " "),
        ("Administrativo", " Administrativo"),
        ("Operacional", "Operacional"),
    )

    funcao_choices = (
        ("", " "),
        ("AUX (ADM)", "AUX (ADM)"),
        ("AUX B1", "AUX B1"),
        ("AUX B2", "AUX B2"),
        ("AUX B3", "AUX B3"),
        ("AUX B4", "AUX B4"),
        ("AUX B5", "AUX B5"),
        ("AUXILIARES", "AUXILIARES"),
        ("B.EDUCADOR", "B.EDUCADOR"),
        ("CH DE SETOR", "CH DE SETOR"),
        ("CH SAT", "CH SAT"),
        ("CH SEC ADM", "CH SEC ADM"),
        ("CH_SEÇÃO", "CH_SEÇÃO"),
        ("CMT", "CMT"),
        ("CMT 1ºSGB", "CMT 1ºSGB"),
        ("AUX (MOTOMEC)", "AUX (MOTOMEC)"),
        ("CMT 2ºSGB", "CMT 2ºSGB"),
        ("CMT 3ºSGB", "CMT 3ºSGB"),
        ("CMT 4ºSGB", "CMT 4ºSGB"),
        ("CMT 5ºSGB", " CMT 5ºSGB"),
        ("CMT PRONTIDÃO", "CMT PRONTIDÃO"),
        ("CMT_BASE", "CMT_BASE"),
        ("CMT_GB", "CMT_GB"),
        ("CMT_PB", "CMT_PB"),
        ("COBOM (ATENDENTE)", "COBOM (ATENDENTE)"),
        ("COBOM (DESPACHADOR)", "COBOM (DESPACHADOR)"),
        ("AUX (NAT)", "3 - AUX (NAT)"),
        ("COBOM (SUPERVISOR)", "COBOM (SUPERVISOR)"),
        ("ESB", "ESB"),
        ("ESSGT", "ESSGT"),
        ("LSV", "LSV"),
        ("LTS", "LTS"),
        ("MECÂNICO", "MECÂNICO"),
        ("MOTORISTA", "MOTORISTA"),
        ("OBRAS", "OBRAS"),
        ("AUX (SAT)", "AUX (SAT)"),
        ("S/FUNÇ_CAD", "S/FUNÇ_CAD"),
        ("TELEFONISTA", "TELEFONISTA"),
        ("TELEMÁTICA", "TELEMÁTICA"),
        ("AUX (SJD)", "AUX (SJD)"),
        ("SUBCMT", "SUBCMT"),
        ("AUX (UGE)", "AUX (UGE)"),
    )
    posto_secao_choices = (
        ("", " "),
        ("703150000 - CMT", "CMT"),
        ("703159000 - SUB CMT", "SUB CMT"),
        ("703159100 - SEC ADM", "SEC ADM"),
        ("703159110 - B/1 E B/5", "B/1 E B/5"),
        ("703159110-1 - B/5", "B/5"),
        ("703159120 - AA", "AA"),
        ("703159130 - B/3 E MOTOMEC", "B/3 E MOTOMEC"),
        ("703159130-1 - MOTOMEC", "MOTOMEC"),
        ("703159131 - COBOM", "COBOM"),
        ("703159140 - B/4", "B/4"),
        ("703159150 - ST UGE", "ST UGE"),
        ("703159160 - ST PJMD", "ST PJMD"),
        ("703159200 - SEC ATIV TEC", "SEC ATIV TEC"),
        ("703151000 - CMT 1º SGB", "CMT 1º SGB"),
        ("703151100 - ADM PB CERRADO", "ADM PB CERRADO"),
        ("703151101 - EB CERRADO", "EB CERRADO"),
        ("703151102 - EB ZONA NORTE", "EB ZONA NORTE"),
        ("703151200 - ADM PB SANTA ROSÁLIA", "ADM PB SANTA ROSÁLIA"),
        ("703151201 - EB SANTA ROSÁLIA", "EB SANTA ROSÁLIA"),
        ("703151202 - EB ÉDEM", "EB ÉDEM"),
        ("703151300 - ADM PB VOTORANTIM", "ADM PB VOTORANTIM"),
        ("703151301 - EB VOTORANTIM", "EB VOTORANTIM"),
        ("703151302 - EB PIEDADE", "EB PIEDADE"),
        ("703151800 - ADM 1º SGB", "ADM 1º SGB"),
        ("703152000 - CMT 2º SGB", "CMT 2º SGB"),
        ("703152100 - ADM PB ITU", "ADM PB ITU"),
        ("703152101 - EB ITU", "EB ITU"),
        ("703152102 - EB PORTO FELIZ", "EB PORTO FELIZ"),
        ("703152200 - ADM PB SALTO", "ADM PB SALTO"),
        ("703152201 - EB SALTO", "EB SALTO"),
        ("703152300 - ADM PB SÃO ROQUE", "ADM PB SÃO ROQUE"),
        ("703152301 - EB SÃO ROQUE", "EB SÃO ROQUE"),
        ("703152302 - EB IBIÚNA", "EB IBIÚNA"),
        ("703152800 - ADM 2º SGB", "ADM 2º SGB"),
        ("703152900 - NUCL ATIV TEC 2º SGB", "NUCL ATIV TEC 2º SGB"),
        ("703153000 - CMT 3º SGB", "CMT 3º SGB"),
        ("703153100 - ADM PB ITAPEVA", "ADM PB ITAPEVA"),
        ("703153101 - EB ITAPEVA", "EB ITAPEVA"),
        ("703153102 - EB APIAÍ", "EB APIAÍ"),
        ("703153103 - EB ITARARÉ", "EB ITARARÉ"),
        ("703153104 - EB CAPÃO BONITO", "EB CAPÃO BONITO"),
        ("703153800 - ADM 3º SGB", "ADM 3º SGB"),
        ("703153900 - NUCL ATIV TEC 3º SGB", "NUCL ATIV TEC 3º SGB"),
        ("703154000 - CMT 4º SGB", "CMT 4º SGB"),
        ("703154100 - ADM PB ITAPETININGA", "ADM PB ITAPETININGA"),
        ("703154101 - EB ITAPETININGA", "EB ITAPETININGA"),
        ("703154102 - EB BOITUVA", "EB BOITUVA"),
        ("703154103 - EB ANGATUBA", "EB ANGATUBA"),
        ("703154200 - ADM PB TATUÍ", "ADM PB TATUÍ"),
        ("703154201 - EB TATUÍ", "EB TATUÍ"),
        ("703154202 - EB TIETÊ", "EB TIETÊ"),
        ("703154203 - EB LARANJAL PAULISTA", "EB LARANJAL PAULISTA"),
        ("703154800 - ADM 4º SGB", "ADM 4º SGB"),
        ("703154900 - NUCL ATIV TEC 4º SGB", "NUCL ATIV TEC 4º SGB"),
        ("703155000 - CMT 5º SGB", "CMT 5º SGB"),
        ("703155100 - ADM PB BOTUCATU", "ADM PB BOTUCATU"),
        ("703155101 - EB BOTUCATU", "EB BOTUCATU"),
        ("703155102 - EB ITATINGA", "EB ITATINGA"),
        ("703155200 - ADM PB AVARÉ", "ADM PB AVARÉ"),
        ("703155201 - EB AVARÉ", "EB AVARÉ"),
        ("703155202 - EB PIRAJU", "EB PIRAJU"),
        ("703155203 - EB ITAÍ", "EB ITAÍ"),
        ("703155800 - ADM 5º SGB", "ADM 5º SGB"),
        ("703155900 - NUCL ATIV TEC 5º SGB", "NUCL ATIV TEC 5º SGB"),
    )

    esta_adido_choices = (
        ("", " "),
        ("703150000 - CMT", "CMT"),
        ("703159000 - SUB CMT", "SUB CMT"),
        ("703159100 - SEC ADM", "SEC ADM"),
        ("703159110 - B/1 E B/5", "B/1 E B/5"),
        ("703159110-1 - B/5", "B/5"),
        ("703159120 - AA", "AA"),
        ("703159130 - B/3 E MOTOMEC", "B/3 E MOTOMEC"),
        ("703159130-1 - MOTOMEC", "MOTOMEC"),
        ("703159131 - COBOM", "COBOM"),
        ("703159140 - B/4", "B/4"),
        ("703159150 - ST UGE", "ST UGE"),
        ("703159160 - ST PJMD", "ST PJMD"),
        ("703159200 - SEC ATIV TEC", "SEC ATIV TEC"),
        ("703151000 - CMT 1º SGB", "CMT 1º SGB"),
        ("703151100 - ADM PB CERRADO", "ADM PB CERRADO"),
        ("703151101 - EB CERRADO", "EB CERRADO"),
        ("703151102 - EB ZONA NORTE", "EB ZONA NORTE"),
        ("703151200 - ADM PB SANTA ROSÁLIA", "ADM PB SANTA ROSÁLIA"),
        ("703151201 - EB SANTA ROSÁLIA", "EB SANTA ROSÁLIA"),
        ("703151202 - EB ÉDEM", "EB ÉDEM"),
        ("703151300 - ADM PB VOTORANTIM", "ADM PB VOTORANTIM"),
        ("703151301 - EB VOTORANTIM", "EB VOTORANTIM"),
        ("703151302 - EB PIEDADE", "EB PIEDADE"),
        ("703151800 - ADM 1º SGB", "ADM 1º SGB"),
        ("703152000 - CMT 2º SGB", "CMT 2º SGB"),
        ("703152100 - ADM PB ITU", "ADM PB ITU"),
        ("703152101 - EB ITU", "EB ITU"),
        ("703152102 - EB PORTO FELIZ", "EB PORTO FELIZ"),
        ("703152200 - ADM PB SALTO", "ADM PB SALTO"),
        ("703152201 - EB SALTO", "EB SALTO"),
        ("703152300 - ADM PB SÃO ROQUE", "ADM PB SÃO ROQUE"),
        ("703152301 - EB SÃO ROQUE", "EB SÃO ROQUE"),
        ("703152302 - EB IBIÚNA", "EB IBIÚNA"),
        ("703152800 - ADM 2º SGB", "ADM 2º SGB"),
        ("703152900 - NUCL ATIV TEC 2º SGB", "NUCL ATIV TEC 2º SGB"),
        ("703153000 - CMT 3º SGB", "CMT 3º SGB"),
        ("703153100 - ADM PB ITAPEVA", "ADM PB ITAPEVA"),
        ("703153101 - EB ITAPEVA", "EB ITAPEVA"),
        ("703153102 - EB APIAÍ", "EB APIAÍ"),
        ("703153103 - EB ITARARÉ", "EB ITARARÉ"),
        ("703153104 - EB CAPÃO BONITO", "EB CAPÃO BONITO"),
        ("703153800 - ADM 3º SGB", "ADM 3º SGB"),
        ("703153900 - NUCL ATIV TEC 3º SGB", "NUCL ATIV TEC 3º SGB"),
        ("703154000 - CMT 4º SGB", "CMT 4º SGB"),
        ("703154100 - ADM PB ITAPETININGA", "ADM PB ITAPETININGA"),
        ("703154101 - EB ITAPETININGA", "EB ITAPETININGA"),
        ("703154102 - EB BOITUVA", "EB BOITUVA"),
        ("703154103 - EB ANGATUBA", "EB ANGATUBA"),
        ("703154200 - ADM PB TATUÍ", "ADM PB TATUÍ"),
        ("703154201 - EB TATUÍ", "EB TATUÍ"),
        ("703154202 - EB TIETÊ", "EB TIETÊ"),
        ("703154203 - EB LARANJAL PAULISTA", "EB LARANJAL PAULISTA"),
        ("703154800 - ADM 4º SGB", "ADM 4º SGB"),
        ("703154900 - NUCL ATIV TEC 4º SGB", "NUCL ATIV TEC 4º SGB"),
        ("703155000 - CMT 5º SGB", "CMT 5º SGB"),
        ("703155100 - ADM PB BOTUCATU", "ADM PB BOTUCATU"),
        ("703155101 - EB BOTUCATU", "EB BOTUCATU"),
        ("703155102 - EB ITATINGA", "EB ITATINGA"),
        ("703155200 - ADM PB AVARÉ", "ADM PB AVARÉ"),
        ("703155201 - EB AVARÉ", "EB AVARÉ"),
        ("703155202 - EB PIRAJU", "EB PIRAJU"),
        ("703155203 - EB ITAÍ", "EB ITAÍ"),
        ("703155800 - ADM 5º SGB", "ADM 5º SGB"),
        ("703155900 - NUCL ATIV TEC 5º SGB", "NUCL ATIV TEC 5º SGB"),
    )

    cat_efetivo_choices = (
        ("", " "),
        ("ATIVO", "ATIVO"),
        ("INATIVO", "INATIVO"),
        ("LSV", "LSV"),
        ("LTS", "LTS"),
        ("LTS FAMILIA", "LTS FAMILIA"),
        ("CONVAL", "CONVAL"),
        ("ELEIÇÃO", "ELEIÇAO"),
        ("LP", "LP"),
        ("FERIAS", "FÉRIAS"),
        ("RESTRICAO", "RESTRIÇÃO"),
    )
    prontidao_choices = (
        ("", " "),
        ("VERDE", "VERDE"),
        ("AMARELA", "AMARELA"),
        ("AZUL", "AZUL"),
        ("ADM", "ADM"),
    )

    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.CASCADE, related_name="detalhes_situacao"
    )
    # Modificado para permitir em branco/nulo
    situacao = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        choices=situacao_choices,
        default="Efetivo",
    )
    # Modificado para permitir em branco/nulo
    cat_efetivo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=cat_efetivo_choices,
        default="ATIVO",
    )
    # Modificado para permitir em branco/nulo
    sgb = models.CharField(max_length=9, blank=True, null=True, choices=sgb_choices)
    # Modificado para permitir em branco/nulo
    posto_secao = models.CharField(
        max_length=100, blank=True, null=True, choices=posto_secao_choices
    )
    esta_adido = models.CharField(
        max_length=100, blank=True, null=True, choices=esta_adido_choices
    )
    # Modificado para permitir em branco/nulo
    funcao = models.CharField(
        max_length=50, blank=True, null=True, choices=funcao_choices
    )
    op_adm = models.CharField(
        max_length=18, blank=True, null=True, choices=op_adm_choices
    )
    # Modificado para permitir em branco/nulo (o default="" já ajuda no blank=True, mas null=True é para o BD)
    prontidao = models.CharField(
        max_length=18, blank=True, null=True, choices=prontidao_choices, default="VERDE"
    )  # Sugestão: um default mais significativo, como "VERDE"
    apresentacao_na_unidade = models.DateField(blank=True, null=True)
    saida_da_unidade = models.DateField(blank=True, null=True)
    data_alteracao = models.DateTimeField(
        auto_now_add=True
    )  # Geralmente não é alterado pelo usuário
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalhes_usuario",
    )

    def __str__(self):
        return f"{self.cadastro.re} - {self.situacao}"

    @property
    def tempo_na_unidade(self):
        hoje = datetime.today()
        delta = relativedelta(hoje, self.apresentacao_na_unidade)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    class Meta:
        indexes = [
            models.Index(fields=["situacao", "posto_secao"]),
            models.Index(fields=["cadastro"]),
        ]
        ordering = ["-data_alteracao"]  # Ordena do mais recente para o mais antigo

    @property
    def status(self):
        if self.situacao == "Efetivo":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">Efetivo</span>'
            )
        if self.situacao == "Exonerado a Pedido":
            return mark_safe(
                '<span class="bg-gray-500 text-white px-2 py-1 rounded">Exonerado a Pedido</span>'
            )
        if self.situacao == "Exonerado Ex-Ofício":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Exonerado Ex-Ofício</span>'
            )
        if self.situacao == "Reserva a Pedido":
            return mark_safe(
                '<span class="bg-indigo-500 text-white px-2 py-1 rounded">Reserva a Pedido</span>'
            )
        if self.situacao == "Transferido":
            return mark_safe(
                '<span class="bg-yellow-500 text-white px-2 py-1 rounded">Transferido</span>'
            )
        if self.situacao == "Mov. Interna":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Mov. Interna</span>'
            )

    @property
    def prontidao_badge(self):
        if self.prontidao == "VERDE":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">VERDE</span>'
            )
        if self.prontidao == "AMARELA":
            return mark_safe(
                '<span class="bg-yellow-500 text-black px-2 py-1 rounded">AMARELA</span>'
            )  # changed text to black for better visibility
        if self.prontidao == "AZUL":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">AZUL</span>'
            )
        if self.prontidao == "ADM":
            return mark_safe(
                '<span class="bg-gray-500 text-white px-2 py-1 rounded">ADM</span>'
            )
        return mark_safe(
            '<span class="bg-gray-200 text-gray-500 px-2 py-1 rounded">N/A</span>'
        )  # added a default badge for empty values.

    @property
    def status_cat(self):
        if self.cat_efetivo == "ATIVO":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">Ativo</span>'
            )
        if self.cat_efetivo == "INATIVO":
            return mark_safe(
                '<span class="bg-gray-500 text-white px-2 py-1 rounded">Inativo</span>'
            )
        if self.cat_efetivo == "LSV":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Lsv</span>'
            )
        if self.cat_efetivo == "LTS":
            return mark_safe(
                '<span class="bg-indigo-500 text-white px-2 py-1 rounded">Lts</span>'
            )
        if self.cat_efetivo == "LTS FAMILIA":
            return mark_safe(
                '<span class="bg-yellow-500 text-white px-2 py-1 rounded">Lts Familia</span>'
            )
        if self.cat_efetivo == "CONVAL":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Conval</span>'
            )
        if self.cat_efetivo == "ELEIÇÃO":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Eleição</span>'
            )
        if self.cat_efetivo == "LP":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">LP</span>'
            )
        if self.cat_efetivo == "FERIAS":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Férias</span>'
            )

    # Adicione ao final da classe DetalhesSituacao
    def get_search_result(self):
        return {
            "title": f"Situação de {self.cadastro.nome_de_guerra}",
            "fields": {
                "Situação": self.situacao,
                "SGB": self.sgb,
                "Posto/Seção": self.posto_secao,
                "Função": self.funcao,
            },
        }


# responsavel pelas promoções de militares


class Promocao(models.Model):
    posto_grad_choices = (
        ("", " "),
        ("Cel PM", "Cel PM"),
        ("Ten Cel PM", "Ten Cel PM"),
        ("Maj PM", "Maj PM"),
        ("CAP PM", "Cap PM"),
        ("1º Ten PM", "1º Ten PM"),
        ("1º Ten QAPM", "1º Ten QAOPM"),
        ("2º Ten PM", "2º Ten PM"),
        ("2º Ten QAPM", "2º Ten QAOPM"),
        ("Asp OF PM", "Asp OF PM"),
        ("Subten PM", "Subten PM"),
        ("1º Sgt PM", "1º Sgt PM"),
        ("2º Sgt PM", "2º Sgt PM"),
        ("3º Sgt PM", "3º Sgt PM"),
        ("Cb PM", "Cb PM"),
        ("Sd PM", "Sd PM"),
        ("Sd PM 2ºCL", "Sd PM 2ºCL"),
    )

    quadro_choices = (
        ("", " "),
        ("Oficiais", "Oficiais"),
        ("Praças Especiais", "Praças Especiais"),
        ("Praças", "Praças"),
    )

    grupo_choices = (
        ("", " "),
        ("Cel", " Cel"),
        ("Tc", "Tc"),
        ("Maj", "Maj"),
        ("Cap", "Cap"),
        ("Ten", "Ten"),
        ("Ten QAOPM", "Ten QAOPM"),
        ("Praça Especiais", "Praça Especiais"),
        ("St/Sgt", "St/Sgt"),
        ("Cb/Sd", "Cb/Sd"),
    )
    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.CASCADE, related_name="promocoes"
    )
    posto_grad = models.CharField(max_length=100, choices=posto_grad_choices)
    quadro = models.CharField(max_length=100, choices=quadro_choices)
    grupo = models.CharField(max_length=100, choices=grupo_choices)
    ultima_promocao = models.DateField(blank=False, null=False)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.cadastro} - {self.posto_grad}"

    @property
    def grad(self):
        if self.posto_grad == "Cel PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Cel PM</span>'
            )
        if self.posto_grad == "Ten Cel PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Ten Cel PM</span>'
            )
        if self.posto_grad == "Maj PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Maj PM</span>'
            )
        if self.posto_grad == "CAP PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">CAP PM</span>'
            )
        if self.posto_grad == "1º Ten PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">1º Ten PM</span>'
            )
        if self.posto_grad == "1º Ten QAPM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">1º Ten QAPM</span>'
            )
        if self.posto_grad == "2º Ten PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">2º Ten PM</span>'
            )
        if self.posto_grad == "2º Ten QAPM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">2º Ten QAPM</span>'
            )
        if self.posto_grad == "Asp OF PM":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">Asp OF PM</span>'
            )
        if self.posto_grad == "Subten PM":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">Subten PM</span>'
            )
        if self.posto_grad == "1º Sgt PM":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">1º Sgt PM</span>'
            )
        if self.posto_grad == "2º Sgt PM":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">2º Sgt PM</span>'
            )
        if self.posto_grad == "3º Sgt PM":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">3º Sgt PM</span>'
            )
        if self.posto_grad == "Cb PM":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Cb PM</span>'
            )
        if self.posto_grad == "Sd PM":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Sd PM</span>'
            )
        if self.posto_grad == "Sd PM 2ºCL":
            return mark_safe(
                '<span class="bg-black text-white px-2 py-1 rounded">Sd PM 2ºCL</span>'
            )

    @property
    def ultima_promocao_detalhada(self):
        hoje = datetime.today()
        delta = relativedelta(hoje, self.ultima_promocao)
        return f"{delta.years} anos, {delta.months} meses e {delta.days} dias"

    class Meta:
        indexes = [
            models.Index(fields=["grupo"]),
            models.Index(fields=["cadastro"]),
        ]

    def get_search_result(self):
        return {
            "title": f"Promoção de {self.cadastro.nome_de_guerra}",
            "fields": {
                "Posto/Grad": self.posto_grad,
                "Última Promoção": self.ultima_promocao.strftime("%d/%m/%Y"),
            },
        }


from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# from backend.efetivo.utils import add_cpf_to_image # Certifique-se de que isso está importado se for usado


class Imagem(models.Model):
    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.CASCADE, related_name="imagens"
    )
    image = models.ImageField(upload_to="img/fotos_perfil")
    create_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        # Adicione esta linha para ordenar as imagens pela data de criação (mais recente primeiro)
        ordering = ["-create_at"]

    def __str__(self):
        return f"Imagem de {self.cadastro.nome_de_guerra}"


class HistoricoPromocao(models.Model):
    cadastro = models.ForeignKey(Cadastro, on_delete=models.CASCADE)
    posto_grad = models.CharField(max_length=100)
    quadro = models.CharField(max_length=100)
    grupo = models.CharField(max_length=100)
    ultima_promocao = models.DateField()
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.cadastro.re} - {self.posto_grad}"


# modelo de dados para  gerar o historico de movimentações  do militar


class HistoricoDetalhesSituacao(models.Model):
    cadastro = models.ForeignKey(
        "Cadastro", on_delete=models.CASCADE
    )  # Use 'Cadastro' como string se Cadastro for definido abaixo
    situacao = models.CharField(
        max_length=50, blank=True, null=True
    )  # Adicionado blank=True, null=True
    sgb = models.CharField(
        max_length=50, blank=True, null=True
    )  # Adicionado blank=True, null=True
    posto_secao = models.CharField(
        max_length=50, blank=True, null=True
    )  # Adicionado blank=True, null=True
    esta_adido = models.CharField(
        max_length=50, blank=True, null=True
    )  # Já era nullable
    funcao = models.CharField(
        max_length=50, blank=True, null=True
    )  # Adicionado blank=True, null=True
    op_adm = models.CharField(
        max_length=50, blank=True, null=True
    )  # Adicionado blank=True, null=True
    prontidao = models.CharField(
        max_length=18, blank=True, null=True, default=""
    )  # blank=True, null=True
    cat_efetivo = models.CharField(
        max_length=30, blank=True, null=True, default="ATIVO"
    )  # blank=True, null=True
    apresentacao_na_unidade = models.DateField(
        blank=True, null=True
    )  # Adicionado blank=True, null=True
    saida_da_unidade = models.DateField(null=True, blank=True)  # Já era nullable
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )  # Usar get_user_model() é mais robusto

    def __str__(self):
        return f'Histórico para {self.cadastro.nome_de_guerra if self.cadastro else "Militar Desconhecido"} - {self.situacao}'

    class Meta:
        verbose_name = "Histórico de Detalhes de Situação"
        verbose_name_plural = "Históricos de Detalhes de Situação"
        ordering = ["-data_alteracao"]  # Boa prática para históricos


from django.db import models
from backend.efetivo.models import Cadastro


class CatEfetivo(models.Model):
    # Choices para o tipo de situação
    TIPO_CHOICES = (
        ("ATIVO", "ATIVO"),
        ("INATIVO", "INATIVO"),
        ("LSV", "LSV"),
        ("LTS", "LTS"),
        ("LTS FAMILIA", "LTS FAMILIA"),
        ("CONVAL", "CONVAL"),
        ("ELEIÇÃO", "ELEIÇÃO"),
        ("LP", "LP"),
        ("FERIAS", "FÉRIAS"),
        ("RESTRICAO", "RESTRIÇÃO"),
        ("DS", "DS"),
        ("DR", "DR"),
        ("FOLGA_MENSAL", "FOLGA MENSAL"),  # NOVO TIPO
        ("FOLGA_SEMANAL", "FOLGA SEMANAL"),  # NOVO TIPO
    )

    # Campos comuns a todos os tipos
    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.CASCADE, related_name="categorias_efetivo"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="ATIVO")
    data_inicio = models.DateField(null=True, blank=True)
    data_termino = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ativo = models.BooleanField(default=True)
    observacao = models.TextField(blank=True, null=True)

    # Campos específicos para LSV
    boletim_concessao_lsv = models.CharField(max_length=50, blank=True, null=True)
    data_boletim_lsv = models.DateField(blank=True, null=True)
    # Campos booleanos para cada tipo de restrição
    restricao_au = models.BooleanField("Audição seja primordial", default=False)
    restricao_ou = models.BooleanField("Ordem unida", default=False)
    restricao_bs = models.BooleanField("Busca e salvamento", default=False)
    restricao_po = models.BooleanField("Policiamento", default=False)
    restricao_cb = models.BooleanField("Corte de barba", default=False)
    restricao_pq = models.BooleanField("Serviços com produtos químicos", default=False)
    restricao_cc = models.BooleanField("Corte de cabelo", default=False)
    restricao_pt = models.BooleanField("Prática de tiro", default=False)
    restricao_ci = models.BooleanField("Correr para incêndio", default=False)
    restricao_sa = models.BooleanField("Serviços aquáticos", default=False)
    restricao_dg = models.BooleanField("Datilografia e Digitação", default=False)
    restricao_sb = models.BooleanField("Serviços burocráticos", default=False)
    restricao_dv = models.BooleanField("Dirigir veículo", default=False)
    restricao_se = models.BooleanField("Serviços externos", default=False)
    restricao_ef = models.BooleanField("Educação Física", default=False)
    restricao_sg = models.BooleanField("Serviço de guarda", default=False)
    restricao_em = models.BooleanField("Escrever a mão", default=False)
    restricao_sh = models.BooleanField("Serviços em altura", default=False)
    restricao_ep = models.BooleanField("Equilíbrio seja primordial", default=False)
    restricao_si = models.BooleanField("Serviços internos", default=False)
    restricao_es = models.BooleanField("Exposição ao sol", default=False)
    restricao_sm = models.BooleanField("Serviços manuais", default=False)
    restricao_fo = models.BooleanField("Formatura", default=False)
    restricao_sn = models.BooleanField("Serviços noturnos", default=False)
    restricao_is = models.BooleanField("Tocar instrumento de sopro", default=False)
    restricao_sp = models.BooleanField("Serviços pesados", default=False)
    restricao_lp = models.BooleanField("Longa permanência em pé", default=False)
    restricao_st = models.BooleanField("Serviços de telefonia", default=False)
    restricao_lr = models.BooleanField("Locais ruidosos", default=False)
    restricao_ua = models.BooleanField("Uso de arma", default=False)
    restricao_ls = models.BooleanField("Longa permanência sentado", default=False)
    restricao_ub = models.BooleanField("Uso de botas", default=False)
    restricao_uc = models.BooleanField("Uso de calçado esportivo", default=False)
    restricao_ma = models.BooleanField("Manuseio com animais", default=False)
    restricao_mc = models.BooleanField("Montar a cavalo", default=False)
    restricao_mg = models.BooleanField("Mergulho", default=False)
    restricao_mp = models.BooleanField("Manipulação de pó", default=False)
    restricao_vp = models.BooleanField("Visão seja primordial", default=False)
    restricao_uu = models.BooleanField("Uso de uniformes", default=False)

    def __str__(self):
        return f"{self.cadastro.nome_de_guerra} - {self.get_tipo_display()} ({self.data_inicio} a {self.data_termino or 'Presente'})"

    @property
    def status(self):
        hoje = date.today()

        # Se não há data de início, retorna status desconhecido
        if not self.data_inicio:
            return "N/A"

        # Se tem data de término e já passou
        if self.data_termino and self.data_termino < hoje:
            return "ENCERRADO"

        # Se a data de início é no futuro
        if self.data_inicio > hoje:
            return "AGUARDANDO INÍCIO"

        # Se está entre as datas ou sem data de término
        return "EM VIGOR"

    @property
    def status_badge(self):
        status = self.status
        if status == "ENCERRADO":
            return mark_safe(
                '<span class="bg-gray-500 text-white px-2 py-1 rounded">ENCERRADO</span>'
            )
        elif status == "AGUARDANDO INÍCIO":
            return mark_safe(
                '<span class="bg-yellow-500 text-black px-2 py-1 rounded">AGUARDANDO INÍCIO</span>'
            )
        elif status == "EM VIGOR":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">EM VIGOR</span>'
            )
        else:  # N/A
            return mark_safe(
                '<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded">N/A</span>'
            )

    def get_total_dias(self):
        if self.data_inicio and self.data_termino:
            # Calcula a diferença em dias. Adicionamos +1 para incluir o dia de início e o dia de término.
            return (self.data_termino - self.data_inicio).days + 1
        return 0

    @property
    def restricoes_selecionadas(self):
        """
        Retorna os campos de restrição como uma lista de dicionários,
        incluindo o nome do campo, verbose_name e o valor (True/False).
        """
        restricao_campos = [
            f for f in self._meta.get_fields() if f.name.startswith("restricao_")
        ]
        return [
            {
                "name": campo.name,
                "verbose_name": campo.verbose_name,
                "value": getattr(self, campo.name),
            }
            for campo in restricao_campos
        ]

    @property
    def tipo_badge(self):
        tipo = self.tipo
        if tipo == "ATIVO":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">ATIVO</span>'
            )
        elif tipo == "INATIVO":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">INATIVO</span>'
            )
        elif tipo == "LSV":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">LSV</span>'
            )
        elif tipo == "LTS":
            return mark_safe(
                '<span class="bg-indigo-500 text-white px-2 py-1 rounded">LTS</span>'
            )
        elif tipo == "LTS FAMILIA":
            return mark_safe(
                '<span class="bg-purple-500 text-white px-2 py-1 rounded">LTS FAMILIA</span>'
            )
        elif tipo == "CONVAL":
            return mark_safe(
                '<span class="bg-pink-500 text-white px-2 py-1 rounded">CONVALESCENÇA</span>'
            )
        elif tipo == "ELEIÇÃO":
            return mark_safe(
                '<span class="bg-teal-500 text-white px-2 py-1 rounded">ELEIÇÃO</span>'
            )
        elif tipo == "LP":
            return mark_safe(
                '<span class="bg-orange-500 text-white px-2 py-1 rounded">LP</span>'
            )
        elif tipo == "FERIAS":
            return mark_safe(
                '<span class="bg-yellow-500 text-black px-2 py-1 rounded">FÉRIAS</span>'
            )
        elif tipo == "RESTRICAO":
            return mark_safe(
                '<span class="bg-red-700 text-white px-2 py-1 rounded">RESTRIÇÃO</span>'
            )
        elif tipo == "DS":
            return mark_safe(
                '<span class="bg-lime-500 text-black px-2 py-1 rounded">DS</span>'
            )
        elif tipo == "DR":
            return mark_safe(
                '<span class="bg-cyan-500 text-white px-2 py-1 rounded">DR</span>'
            )
        else:
            return mark_safe(
                f'<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded">{tipo}</span>'
            )

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Verifica se é um novo registro

        # Atualiza status ativo/inativo
        hoje = timezone.now().date()
        if self.data_termino:
            self.ativo = self.data_termino > hoje
        else:
            self.ativo = True

        # Limpa restrições se não for RESTRICAO
        if self.tipo != "RESTRICAO":
            campos_restricao = [
                f.name for f in self._meta.fields if f.name.startswith("restricao_")
            ]
            for campo in campos_restricao:
                setattr(self, campo, False)

        super().save(*args, **kwargs)

        # Cria histórico apenas se for novo
        if is_new:
            self.criar_registro_historico()

    def get_search_result(self):
        return {
            "title": f"{self.get_tipo_display()} - {self.cadastro.nome_de_guerra}",
            "fields": {
                "Tipo": self.get_tipo_display(),
                "Início": self.data_inicio.strftime("%d/%m/%Y"),
                "Término": (
                    self.data_termino.strftime("%d/%m/%Y") if self.data_termino else "-"
                ),
                "Status": self.status,
            },
        }

    @property
    def restricoes_selecionadas(self):
        """Retorna uma lista com as restrições selecionadas"""
        restricoes = []
        campos_restricao = [
            field.name
            for field in self._meta.get_fields()
            if field.name.startswith("restricao_")
        ]

        for campo in campos_restricao:
            if getattr(self, campo):
                # Pega o verbose_name do campo
                verbose_name = self._meta.get_field(campo).verbose_name
                restricoes.append(verbose_name)

        return restricoes

    @property
    def restricoes_selecionadas_siglas(self):
        if self.tipo != "RESTRICAO":
            return ""

        siglas = []
        campos_restricao = [
            field.name
            for field in self._meta.get_fields()
            if field.name.startswith("restricao_")
        ]

        for campo in campos_restricao:
            if getattr(self, campo):
                # Pega as duas últimas letras do nome do campo
                sigla = campo.split("_")[-1].upper()
                siglas.append(sigla)

        return ", ".join(siglas)

    @property
    def restricoes_selecionadas_badges(self):
        """Retorna badges HTML com as restrições selecionadas"""
        badges = []
        for restricao in self.restricoes_selecionadas:
            badges.append(
                f'<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded text-xs mr-1">{restricao}</span>'
            )
        return mark_safe(" ".join(badges))

    def save(self, *args, **kwargs):
        # Verifica se a data de término foi atingida e marca como inativo
        if self.data_termino and self.data_termino < date.today():
            self.ativo = False

        # Se não for do tipo RESTRICAO, limpa todas as restrições
        if self.tipo != "RESTRICAO":
            campos_restricao = [
                field.name
                for field in self._meta.get_fields()
                if field.name.startswith("restricao_")
            ]
            for campo in campos_restricao:
                setattr(self, campo, False)

        # Cria registro no histórico se não for novo ou se houver alterações
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            self.criar_registro_historico()

    def criar_registro_historico(self):
        """Cria um registro no histórico com o estado atual"""
        HistoricoCatEfetivo.objects.create(
            cat_efetivo=self,
            tipo=self.tipo,
            data_inicio=self.data_inicio,
            data_termino=self.data_termino,
            ativo=self.ativo,
            observacao=self.observacao,
            # Campos LSV
            boletim_concessao_lsv=self.boletim_concessao_lsv,
            data_boletim_lsv=self.data_boletim_lsv,
            # Todos os campos de restrição
            restricao_au=self.restricao_au,
            restricao_ou=self.restricao_ou,
            restricao_bs=self.restricao_bs,
            restricao_po=self.restricao_po,
            restricao_cb=self.restricao_cb,
            restricao_pq=self.restricao_pq,
            restricao_cc=self.restricao_cc,
            restricao_pt=self.restricao_pt,
            restricao_ci=self.restricao_ci,
            restricao_sa=self.restricao_sa,
            restricao_dg=self.restricao_dg,
            restricao_sb=self.restricao_sb,
            restricao_dv=self.restricao_dv,
            restricao_se=self.restricao_se,
            restricao_ef=self.restricao_ef,
            restricao_sg=self.restricao_sg,
            restricao_em=self.restricao_em,
            restricao_sh=self.restricao_sh,
            restricao_ep=self.restricao_ep,
            restricao_si=self.restricao_si,
            restricao_es=self.restricao_es,
            restricao_sm=self.restricao_sm,
            restricao_fo=self.restricao_fo,
            restricao_sn=self.restricao_sn,
            restricao_is=self.restricao_is,
            restricao_sp=self.restricao_sp,
            restricao_lp=self.restricao_lp,
            restricao_st=self.restricao_st,
            restricao_lr=self.restricao_lr,
            restricao_ua=self.restricao_ua,
            restricao_ls=self.restricao_ls,
            restricao_ub=self.restricao_ub,
            restricao_uc=self.restricao_uc,
            restricao_ma=self.restricao_ma,
            restricao_mc=self.restricao_mc,
            restricao_mg=self.restricao_mg,
            restricao_mp=self.restricao_mp,
            restricao_vp=self.restricao_vp,
            restricao_uu=self.restricao_uu,
            usuario_alteracao=self.usuario_cadastro,
        )

    class Meta:
        verbose_name = "Categoria de Efetivo"
        verbose_name_plural = "Categorias de Efetivo"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["cadastro"]),
            models.Index(fields=["ativo"]),
            models.Index(fields=["data_inicio", "data_termino"]),
        ]

    @property
    def tipo_icon(self):
        icons = {
            "LSV": "fa-ambulance",
            "LTS": "fa-procedures",
            "LTS FAMILIA": "fa-baby-carriage",
            "CONVAL": "fa-heartbeat",
            "ELEIÇÃO": "fa-vote-yea",
            "LP": "fa-gavel",
            "FERIAS": "fa-umbrella-beach",
            "DS": "fa-calendar-day",
            "DR": "fa-calendar-week",
        }
        return icons.get(self.tipo, "fa-user")

    @property
    def tipo_color(self):
        colors = {
            "LSV": "blue",
            "LTS": "indigo",
            "LTS FAMILIA": "purple",
            "CONVAL": "pink",
            "ELEIÇÃO": "teal",
            "LP": "orange",
            "FERIAS": "yellow",
            "DS": "lime",
            "DR": "cyan",
        }
        return colors.get(self.tipo, "gray")

    @property
    def regras_restricoes_badges(self):
        if self.tipo != "RESTRICAO":
            return mark_safe(
                '<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded text-xs">N/A</span>'
            )

        badges = []

        # Grupo 5.2.1
        grupo_521 = {
            "BS",
            "CI",
            "DV",
            "EF",
            "FO",
            "IS",
            "LP",
            "MA",
            "MC",
            "MG",
            "OU",
            "PO",
            "PQ",
            "SA",
            "SE",
            "SH",
            "SM",
            "SP",
        }
        if any(
            sigla in grupo_521
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-1" title="Atividades operacionais com condições ou administrativas/apoio">5.2.1</span>'
            )

        # Grupo 5.2.1.1 (subgrupo de EF)
        if "EF" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-blue-200 text-blue-800 px-2 py-1 rounded text-xs mr-1" title="Plano de exercícios físicos específicos">5.2.1.1</span>'
            )

        # Grupo 5.2.2
        grupo_522 = {"AU", "EP", "ES", "LR", "PT", "VP"}
        if any(
            sigla in grupo_522
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs mr-1" title="Somente atividades administrativas">5.2.2</span>'
            )

        # Grupo 5.2.3
        if "SN" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs mr-1" title="Trabalhar durante o dia em qualquer atividade">5.2.3</span>'
            )

        # Grupo 5.2.4
        if "SG" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs mr-1" title="Policiamento ostensivo ou administrativas/apoio">5.2.4</span>'
            )

        # Grupo 5.2.5
        if "UA" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-red-100 text-red-800 px-2 py-1 rounded text-xs mr-1" title="Desarmado e atividades administrativas">5.2.5</span>'
            )

        # Grupo 5.2.5.1 (subgrupo de UA)
        if "UA" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-red-200 text-red-800 px-2 py-1 rounded text-xs mr-1" title="Pode requerer processo administrativo">5.2.5.1</span>'
            )

        # Grupo 5.2.6
        grupo_526 = {"UU", "CC", "CB"}
        if any(
            sigla in grupo_526
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs mr-1" title="Atividades administrativas ou de apoio">5.2.6</span>'
            )

        # Grupo 5.2.6.1 (subgrupo de UU, CC, CB)
        if any(
            sigla in grupo_526
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-indigo-200 text-indigo-800 px-2 py-1 rounded text-xs mr-1" title="Uniforme B-5.1, sem atendimento ao público">5.2.6.1</span>'
            )

        # Grupo 5.2.6.2 (subgrupo de CC)
        if "CC" in self.restricoes_selecionadas_siglas:
            badges.append(
                '<span class="bg-indigo-300 text-indigo-800 px-2 py-1 rounded text-xs mr-1" title="Cabelos penteados com gel/rede">5.2.6.2</span>'
            )

        # Grupo 5.2.7
        grupo_527 = {"UB", "UC", "US"}
        if any(
            sigla in grupo_527
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-teal-100 text-teal-800 px-2 py-1 rounded text-xs mr-1" title="Sandálias pretas, sem atendimento ao público">5.2.7</span>'
            )

        # Grupo 5.2.8
        grupo_528 = {"DG", "EM", "LS", "MP", "SB", "SI", "ST"}
        if any(
            sigla in grupo_528
            for sigla in self.restricoes_selecionadas_siglas.split(", ")
        ):
            badges.append(
                '<span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs mr-1" title="Policiamento ostensivo">5.2.8</span>'
            )

        # Grupo 5.2.9 (para gestantes)
        # Nota: Você precisaria ter um campo para identificar gestantes
        # if self.gestante:
        #     badges.append(
        #         '<span class="bg-pink-100 text-pink-800 px-2 py-1 rounded text-xs mr-1" title="Atividades administrativas com uniforme de gestante">5.2.9</span>'
        #     )

        # Grupo 5.2.9.1 (subgrupo de gestantes com US)
        # if self.gestante and 'US' in self.restricoes_selecionadas_siglas:
        #     badges.append(
        #         '<span class="bg-pink-200 text-pink-800 px-2 py-1 rounded text-xs mr-1" title="Sem atendimento ao público">5.2.9.1</span>'
        #     )

        return (
            mark_safe(" ".join(badges))
            if badges
            else mark_safe(
                '<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded text-xs">Sem regras específicas</span>'
            )
        )


@property
def regras_restricoes_badges(self):
    if self.tipo != "RESTRICAO":
        return []

    regras = []
    siglas = (
        self.restricoes_selecionadas_siglas.split(", ")
        if self.restricoes_selecionadas_siglas
        else []
    )

    # Mapeamento de regras para siglas
    regras_map = {
        "5.2.1": [
            "BS",
            "CI",
            "DV",
            "EF",
            "FO",
            "IS",
            "LP",
            "MA",
            "MC",
            "MG",
            "OU",
            "PO",
            "PQ",
            "SA",
            "SE",
            "SH",
            "SM",
            "SP",
        ],
        "5.2.2": ["AU", "EP", "ES", "LR", "PT", "VP"],
        "5.2.3": ["SN"],
        "5.2.4": ["SG"],
        "5.2.5": ["UA"],
        "5.2.6": ["UU", "CC", "CB"],
        "5.2.7": ["UB", "UC", "US"],
        "5.2.8": ["DG", "EM", "LS", "MP", "SB", "SI", "ST"],
    }

    # Verifica quais regras se aplicam
    for regra, siglas_regra in regras_map.items():
        if any(sigla in siglas for sigla in siglas_regra):
            regras.append(regra)

    return regras

    @property
    def get_restricao_fields(self):
        fields_data = []
        for field in self._meta.get_fields():
            if field.name.startswith("restricao_") and isinstance(
                field, models.BooleanField
            ):
                fields_data.append(
                    {
                        "name": field.name,
                        "verbose_name": field.verbose_name,
                        "value": getattr(self, field.name),
                    }
                )
        return fields_data

    @property
    def tipo_choices(self):
        return CatEfetivo._meta.get_field("tipo").choices


class HistoricoCatEfetivo(models.Model):
    cat_efetivo = models.ForeignKey(
        "CatEfetivo", on_delete=models.CASCADE, related_name="historico"
    )  # Usar string para evitar importação circular se CatEfetivo estiver abaixo
    data_registro = models.DateTimeField(auto_now_add=True)
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Campos espelho do CatEfetivo
    tipo = models.CharField(
        max_length=20,
        choices=[  # Definir as escolhas aqui ou referenciar CatEfetivo.TIPO_CHOICES
            ("ATIVO", "Ativo"),
            ("INATIVO", "Inativo"),
            ("LSV", "LSV - Licença para Serviço Voluntário"),
            ("LTS", "LTS - Licença para Tratamento de Saúde"),
            (
                "LTS FAMILIA",
                "LTS Família - Licença para Tratamento de Saúde de Familiar",
            ),
            ("CONVAL", "Convalescença"),
            ("ELEIÇÃO", "Eleição"),
            ("LP", "Licença Prêmio"),
            ("FERIAS", "Férias"),
            ("RESTRICAO", "Restrição"),
            ("DS", "Dispensado de Serviço"),
            ("DR", "Dispensa Recompensa"),
            # ... Adicione outras escolhas se existirem em CatEfetivo.TIPO_CHOICES
        ],
    )
    data_inicio = models.DateField()
    data_termino = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    observacao = models.TextField(blank=True, null=True)
    deletado = models.BooleanField(default=False)  # Adicione este campo
    # Campos LSV
    boletim_concessao_lsv = models.CharField(max_length=50, blank=True, null=True)
    data_boletim_lsv = models.DateField(blank=True, null=True)

    # Campos de restrição (todos como booleanos)
    restricao_au = models.BooleanField("Audição seja primordial", default=False)
    restricao_ou = models.BooleanField("Ordem unida", default=False)
    restricao_bs = models.BooleanField("Busca e salvamento", default=False)
    restricao_po = models.BooleanField("Policiamento", default=False)
    restricao_cb = models.BooleanField("Corte de barba", default=False)
    restricao_pq = models.BooleanField("Serviços com produtos químicos", default=False)
    restricao_cc = models.BooleanField("Corte de cabelo", default=False)
    restricao_pt = models.BooleanField("Prática de tiro", default=False)
    restricao_ci = models.BooleanField("Correr para incêndio", default=False)
    restricao_sa = models.BooleanField("Serviços aquáticos", default=False)
    restricao_dg = models.BooleanField("Datilografia e Digitação", default=False)
    restricao_sb = models.BooleanField("Serviços burocráticos", default=False)
    restricao_dv = models.BooleanField("Dirigir veículo", default=False)
    restricao_se = models.BooleanField("Serviços externos", default=False)
    restricao_ef = models.BooleanField("Educação Física", default=False)
    restricao_sg = models.BooleanField("Serviço de guarda", default=False)
    restricao_em = models.BooleanField("Escrever a mão", default=False)
    restricao_sh = models.BooleanField("Serviços em altura", default=False)
    restricao_ep = models.BooleanField("Equilíbrio seja primordial", default=False)
    restricao_si = models.BooleanField("Serviços internos", default=False)
    restricao_es = models.BooleanField("Exposição ao sol", default=False)
    restricao_sm = models.BooleanField("Serviços manuais", default=False)
    restricao_fo = models.BooleanField("Formatura", default=False)
    restricao_sn = models.BooleanField("Serviços noturnos", default=False)
    restricao_is = models.BooleanField("Tocar instrumento de sopro", default=False)
    restricao_sp = models.BooleanField("Serviços pesados", default=False)
    restricao_lp = models.BooleanField("Longa permanência em pé", default=False)
    restricao_st = models.BooleanField("Serviços de telefonia", default=False)
    restricao_lr = models.BooleanField("Locais ruidosos", default=False)
    restricao_ua = models.BooleanField("Uso de arma", default=False)
    restricao_ls = models.BooleanField("Longa permanência sentado", default=False)
    restricao_ub = models.BooleanField("Uso de botas", default=False)
    restricao_uc = models.BooleanField("Uso de calçado esportivo", default=False)
    restricao_ma = models.BooleanField("Manuseio com animais", default=False)
    restricao_mc = models.BooleanField("Montar a cavalo", default=False)
    restricao_mg = models.BooleanField("Mergulho", default=False)
    restricao_mp = models.BooleanField("Manipulação de pó", default=False)
    restricao_vp = models.BooleanField("Visão seja primordial", default=False)
    restricao_uu = models.BooleanField("Uso de uniformes", default=False)

    def __str__(self):
        return f"Histórico {self.cat_efetivo} - {self.data_registro.strftime('%d/%m/%Y %H:%M')}"

    @property
    def tipo_badge(self):
        # A lógica do tipo_badge está perfeita e pode ser mantida como está.
        # Apenas garantir que mark_safe seja importado.
        tipo = self.tipo
        if tipo == "ATIVO":
            return mark_safe(
                '<span class="bg-green-500 text-white px-2 py-1 rounded">ATIVO</span>'
            )
        elif tipo == "INATIVO":
            return mark_safe(
                '<span class="bg-red-500 text-white px-2 py-1 rounded">INATIVO</span>'
            )
        elif tipo == "LSV":
            return mark_safe(
                '<span class="bg-blue-500 text-white px-2 py-1 rounded">LSV</span>'
            )
        elif tipo == "LTS":
            return mark_safe(
                '<span class="bg-indigo-500 text-white px-2 py-1 rounded">LTS</span>'
            )
        elif tipo == "LTS FAMILIA":
            return mark_safe(
                '<span class="bg-purple-500 text-white px-2 py-1 rounded">LTS FAMILIA</span>'
            )
        elif tipo == "CONVAL":
            return mark_safe(
                '<span class="bg-pink-500 text-white px-2 py-1 rounded">CONVALESCENÇA</span>'
            )
        elif tipo == "ELEIÇÃO":
            return mark_safe(
                '<span class="bg-teal-500 text-white px-2 py-1 rounded">ELEIÇÃO</span>'
            )
        elif tipo == "LP":
            return mark_safe(
                '<span class="bg-orange-500 text-white px-2 py-1 rounded">LP</span>'
            )
        elif tipo == "FERIAS":
            return mark_safe(
                '<span class="bg-yellow-500 text-black px-2 py-1 rounded">FÉRIAS</span>'
            )
        elif tipo == "RESTRICAO":
            return mark_safe(
                '<span class="bg-red-700 text-white px-2 py-1 rounded">RESTRIÇÃO</span>'
            )
        elif tipo == "DS":
            return mark_safe(
                '<span class="bg-lime-500 text-black px-2 py-1 rounded">DS</span>'
            )
        elif tipo == "DR":
            return mark_safe(
                '<span class="bg-cyan-500 text-white px-2 py-1 rounded">DR</span>'
            )
        else:
            return mark_safe(
                f'<span class="bg-gray-200 text-gray-800 px-2 py-1 rounded">{tipo}</span>'
            )

    @property
    def status_info(self):
        hoje = date.today()
        if not self.data_inicio:
            return "N/A"

        if self.data_termino and self.data_termino < hoje:
            return "ENCERRADO"
        elif self.data_inicio > hoje:
            return "AGUARDANDO INÍCIO"
        elif self.data_inicio <= hoje and (
            self.data_termino is None or self.data_termino >= hoje
        ):
            return "EM VIGOR"
        else:
            return "N/A"

    def get_total_dias(self):
        if self.data_inicio and self.data_termino:
            # Calcula a diferença em dias. Adicionamos +1 para incluir o dia de início e o dia de término.
            return (self.data_termino - self.data_inicio).days + 1
        return 0  # Retorna 0 se as datas não estiverem completas para o cálculo

    @property
    def restricoes_selecionadas_siglas(self):
        if self.tipo != "RESTRICAO":
            return ""

        siglas = []
        # Percorre todos os campos do modelo
        for field in self._meta.get_fields():
            # Verifica se o campo é um booleano e começa com 'restricao_'
            if isinstance(field, models.BooleanField) and field.name.startswith(
                "restricao_"
            ):
                # Se o valor do campo booleano for True
                if getattr(self, field.name):
                    # Pega as duas últimas letras do nome do campo (a sigla)
                    sigla = field.name.split("_")[-1].upper()
                    siglas.append(sigla)

        return ", ".join(siglas)

    class Meta:
        verbose_name = "Histórico de Categoria de Efetivo"
        verbose_name_plural = "Históricos de Categorias de Efetivo"
        ordering = ["-data_registro"]
        indexes = [
            models.Index(fields=["cat_efetivo"]),
            models.Index(fields=["data_registro"]),
            models.Index(fields=["tipo"]),
        ]

        # Adicione ao final da classe HistoricoCatEfetivo

    def get_search_result(self):
        return {
            "title": f"Histórico Categoria - {self.cat_efetivo.cadastro.nome_de_guerra}",
            "fields": {
                "Tipo": self.get_tipo_display(),
                "Data Registro": self.data_registro.strftime("%d/%m/%Y %H:%M"),
                "Status": self.status_info,
            },
        }
