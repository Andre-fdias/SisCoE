// main.js
console.log('Teste')

function mostrarSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
      spinner.classList.add('active');
    }
  }
  
  function esconderSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
      spinner.classList.remove('active');
    }
  }
  
  document.addEventListener('DOMContentLoaded', function() {
    const meuFormulario = document.getElementById('meu-formulario');
    if (meuFormulario) {
      meuFormulario.addEventListener('submit', function(event) {
        event.preventDefault();
        mostrarSpinner();
        fetch(this.action, {
          method: this.method,
          body: new FormData(this)
        })
        .then(response => response.text())
        .then(data => {
          esconderSpinner();
          const resultadoDiv = document.getElementById('resultado');
          if (resultadoDiv) {
            resultadoDiv.innerHTML = data;
          }
        })
        .catch(error => {
          esconderSpinner();
          console.error('Erro na requisição:', error);
        });
      });
    }
  });