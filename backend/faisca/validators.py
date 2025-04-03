from django.core.exceptions import ValidationError

class QueryValidator:
    @staticmethod
    def validate_query(query):
        """Valida se a consulta é segura e relevante"""
        # Palavras-chave proibidas
        forbidden = ['receita', 'bolo', 'futebol', 'musica', 'google', 'pesquisar']
        if any(word in query.lower() for word in forbidden):
            raise ValidationError("Consulta contém termos não permitidos")
        
        # Deve mencionar pelo menos um app ou modelo conhecido
        known_terms = [app.split('.')[-1] for app in settings.INSTALLED_APPS]
        known_terms += ['militar', 'documento', 'agenda', 'cliente']
        
        if not any(term in query.lower() for term in known_terms):
            raise ValidationError("Consulta não relacionada aos dados do sistema")
        
        return True