#!/usr/bin/env python
# run_tests.py - Sistema unificado de testes para SisCoE
import os
import sys
import django
import argparse
from pathlib import Path


def setup_django():
    """Configura o ambiente Django para testes"""
    project_root = Path(__file__).parent
    sys.path.append(str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")
    django.setup()

    return project_root


def run_tests(apps=None, verbosity=2, failfast=False, coverage=False):
    """Executa os testes"""
    project_root = setup_django()

    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=True, failfast=failfast)

    if coverage:
        import coverage

        cov = coverage.coverage(
            source=["backend"],
            omit=[
                "*/migrations/*",
                "*/tests/*",
                "*/__pycache__/*",
                "*/static/*",
                "*/templates/*",
            ],
        )
        cov.start()

    # Definir apps padrão se não especificadas
    if not apps:
        apps = [
            "backend.accounts",
            "backend.bm",
            "backend.core",
            "backend.efetivo",
            "backend.municipios",
            "backend.rpt",
            "backend.adicional",
            "backend.agenda",
            "backend.calculadora",
            "backend.crm",
            "backend.cursos",
            "backend.documentos",
            "backend.lp",
        ]

    print(f"🧪 Executando testes para {len(apps)} app(s)...")
    failures = test_runner.run_tests(apps)

    if coverage:
        cov.stop()
        cov.save()

        print("\n📊 RELATÓRIO DE COBERTURA:")
        cov.report()

        # Gerar relatório HTML
        html_dir = project_root / "htmlcov"
        cov.html_report(directory=str(html_dir))
        print(f"📁 Relatório HTML gerado em: {html_dir}/index.html")

    return 1 if failures else 0


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sistema de Testes SisCoE")
    parser.add_argument("apps", nargs="*", help="Apps específicos para testar")
    parser.add_argument("--all", action="store_true", help="Testar todos os apps")
    parser.add_argument("--bm", action="store_true", help="Testar apenas app BM")
    parser.add_argument("--core", action="store_true", help="Testar apps core")
    parser.add_argument(
        "--verbosity", type=int, default=2, help="Nível de verbosidade (0-3)"
    )
    parser.add_argument(
        "--failfast", action="store_true", help="Parar no primeiro erro"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Gerar relatório de cobertura"
    )
    parser.add_argument("--list", action="store_true", help="Listar apps disponíveis")

    args = parser.parse_args()

    # Listar apps disponíveis
    if args.list:
        apps_list = [
            "accounts",
            "bm",
            "core",
            "efetivo",
            "municipios",
            "rpt",
            "adicional",
            "agenda",
            "calculadora",
            "crm",
            "cursos",
            "documentos",
            "lp",
        ]
        print("📋 Apps disponíveis para teste:")
        for app in apps_list:
            print(f"  - backend.{app}")
        return

    # Determinar quais apps testar
    apps_to_test = []

    if args.apps:
        apps_to_test = [f"backend.{app}" for app in args.apps]
    elif args.bm:
        apps_to_test = ["backend.bm"]
    elif args.core:
        apps_to_test = ["backend.accounts", "backend.core", "backend.efetivo"]
    elif args.all:
        apps_to_test = None  # Todos os apps
    else:
        # Padrão: testar apps principais
        apps_to_test = ["backend.bm", "backend.core", "backend.accounts"]

    # Executar testes
    result = run_tests(
        apps=apps_to_test,
        verbosity=args.verbosity,
        failfast=args.failfast,
        coverage=args.coverage,
    )

    sys.exit(result)


if __name__ == "__main__":
    main()
