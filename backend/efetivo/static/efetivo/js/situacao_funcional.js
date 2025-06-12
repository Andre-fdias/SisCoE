<script>
// SituacaoFuncional.js - Controle dos modais de situação funcional
document.addEventListener('DOMContentLoaded', function() {
  // Função para mostrar/ocultar modais
  function toggleModal(modalId, show) {
    const modal = document.querySelector(modalId);
    if (modal) {
      modal.classList.toggle('hidden', !show);
    }
  }

  // Fechar modais ao clicar no botão de fechar ou fora
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', function() {
      const modalId = this.getAttribute('data-modal-close');
      toggleModal(modalId, false);
    });
  });

  // Modal 1: Editar Situação Funcional
  const editForm = document.getElementById('editSituacaoForm');
  if (editForm) {
    editForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      try {
        const response = await fetch(this.action, {
          method: 'POST',
          body: new FormData(this),
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': this.querySelector('[name=csrfmiddlewaretoken]').value
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          toggleModal('#editSituacaoModal', false);
          toggleModal('#confirmNovaSituacaoModal', true);
        } else {
          alert(data.message || 'Erro ao processar');
        }
      } catch (error) {
        console.error('Error:', error);
        alert('Erro na requisição');
      }
    });
  }

  // Modal 2: Confirmação
  const confirmForm = document.getElementById('confirmArquivamentoForm');
  if (confirmForm) {
    confirmForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      try {
        const response = await fetch(this.action, {
          method: 'POST',
          body: new FormData(this),
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': this.querySelector('[name=csrfmiddlewaretoken]').value
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          toggleModal('#confirmNovaSituacaoModal', false);
          
          if (data.redirect_url.includes('cadastrar_nova')) {
            toggleModal('#novaSituacaoModal', true);
          } else {
            window.location.href = data.redirect_url;
          }
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  }

  // Modal 3: Nova Situação
  const novaSituacaoForm = document.getElementById('novaSituacaoForm');
  if (novaSituacaoForm) {
    novaSituacaoForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      try {
        const response = await fetch(this.action, {
          method: 'POST',
          body: new FormData(this),
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': this.querySelector('[name=csrfmiddlewaretoken]').value
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          window.location.href = data.redirect_url;
        } else {
          alert(data.message || 'Erro ao salvar');
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  }
});
</script>