from django import template

register = template.Library()

@register.simple_tag
def global_spinner():
    """
    Template tag universal para spinner
    """
    return """
<div id="global-spinner-container" class="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-900 bg-opacity-80 hidden" style="opacity: 0; transition: opacity 0.3s ease;">
    <div class="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center">
        <div class="flex space-x-2 mb-4">
            <div class="w-4 h-4 bg-blue-500 rounded-full animate-bounce"></div>
            <div class="w-4 h-4 bg-green-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="w-4 h-4 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
        </div>
        <p class="text-gray-700 font-medium">SisCoE - Carregando...</p>
    </div>
</div>

<script>
// SPINNER UNIVERSAL - TEMPLATE TAG
(function() {
    'use strict';
    
    // Sistema global unico
    if (typeof window.GlobalSpinner === 'undefined') {
        const spinner = document.getElementById('global-spinner-container');
        
        window.GlobalSpinner = {
            show: function() { 
                if(spinner) {
                    spinner.classList.remove('hidden');
                    setTimeout(() => spinner.style.opacity = '1', 10);
                }
            },
            hide: function() { 
                if(spinner) {
                    spinner.style.opacity = '0';
                    setTimeout(() => spinner.classList.add('hidden'), 300);
                }
            }
        };
        
        // Eventos automaticos
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => GlobalSpinner.hide(), 100);
        });
        
        document.addEventListener('click', function(e) {
            const target = e.target.closest('a');
            if (target && target.href && !target.href.startsWith('javascript:')) {
                GlobalSpinner.show();
            }
        });
        
        window.addEventListener('beforeunload', function() {
            GlobalSpinner.show();
        });
        
        window.addEventListener('load', function() {
            setTimeout(() => GlobalSpinner.hide(), 300);
        });
    }
})();
</script>
"""