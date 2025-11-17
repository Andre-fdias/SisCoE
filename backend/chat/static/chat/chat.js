// backend/chat/static/chat/chat.js
document.addEventListener('DOMContentLoaded', function() {

    // --- UI ELEMENTS ---
    const ui = {
        chatContainer: document.getElementById('chat-container'),
        sidebar: {
            container: document.getElementById('conversations-sidebar'),
            newConversationBtn: document.getElementById('new-conversation-btn'),
            tabs: document.querySelectorAll('.sidebar-tab'),
            searchInput: document.getElementById('sidebar-search'),
            conversationList: document.getElementById('conversation-list-container'),
            groupList: document.getElementById('group-list-container'),
            contactList: document.getElementById('contact-list-container'),
        },
        main: document.querySelector('.flex-1.flex-col'),
        activeConversation: {
            container: document.getElementById('active-conversation'),
            backBtn: document.getElementById('back-to-conversations'),
            avatar: document.getElementById('conversation-avatar'),
            status: document.getElementById('conversation-status'),
            name: document.getElementById('conversation-name'),
            presence: document.getElementById('conversation-presence'),
            infoBtn: document.getElementById('conversation-info-btn'),
        },
        initialScreen: document.getElementById('no-conversation-selected'),
        message: {
            area: document.getElementById('message-area'),
            list: document.getElementById('message-list'),
            form: document.getElementById('message-form'),
            input: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            attachFileBtn: document.getElementById('attach-file-btn'),
            fileInput: document.getElementById('file-input'),
        },
        filePreview: {
            container: document.getElementById('file-preview-container'),
            name: document.getElementById('file-preview-name'),
            removeBtn: document.getElementById('remove-file-btn'),
        },
        infoModal: {
            container: document.getElementById('conversation-info-modal'),
            content: document.getElementById('info-modal-content'),
            closeBtn: document.getElementById('close-info-modal-btn'),
            loading: document.getElementById('info-modal-loading'),
            data: document.getElementById('info-modal-data'),
            img: document.getElementById('info-modal-img'),
            avatarPlaceholder: document.getElementById('info-modal-avatar-placeholder'),
            avatarInitial: document.getElementById('info-modal-avatar-initial'),
            name: document.getElementById('info-modal-name'),
            posto: document.getElementById('info-modal-posto'),
            sgbDisplay: document.getElementById('info-modal-sgb-display'),
            re: document.getElementById('info-modal-re'),
            nomeCompleto: document.getElementById('info-modal-nome-completo'),
            sgb: document.getElementById('info-modal-sgb'),
            secao: document.getElementById('info-modal-secao'),
        },
        typingIndicator: {
            container: document.getElementById('typing-indicator'),
            user: document.getElementById('typing-user'),
        },
        toastContainer: document.getElementById('toast-container'),
        templates: {
            conversation: document.getElementById('conversation-item-template'),
            contact: document.getElementById('contact-item-template'),
            group: document.getElementById('group-item-template'),
            messageSent: document.getElementById('message-sent-template'),
            messageReceived: document.getElementById('message-received-template'),
            dateSeparator: document.getElementById('date-separator-template'),
            toast: document.getElementById('toast-template'),
            placeholder: document.getElementById('list-placeholder-template'),
        },
    };

    // --- APPLICATION STATE ---
    const state = {
        currentUser: {
            id: ui.chatContainer?.dataset.userId || null,
            username: ui.chatContainer?.dataset.username || 'Usuário',
            imageUrl: ui.chatContainer?.dataset.userImageUrl || null,
            csrfToken: ui.chatContainer?.dataset.csrfToken || null,
        },
        socket: null,
        activeConversationId: null,
        activeTab: 'conversations',
        conversations: new Map(),
        contacts: [],
        groups: [],
        typingTimeout: null,
        selectedFile: null,
        lastMessageDate: null,
        reconnect: { 
            attempts: 0, 
            maxAttempts: 5, 
            delay: 1000,
            timer: null 
        },
        currentMessageToDelete: null,
        currentConversationToDelete: null,
        activeDropdown: null,
    };

    // --- VERIFICAÇÃO DE ELEMENTOS CRÍTICOS ---
    function validateCriticalElements() {
        const criticalElements = [
            { name: 'chatContainer', element: ui.chatContainer },
            { name: 'sidebar.container', element: ui.sidebar.container },
            { name: 'message.area', element: ui.message.area },
            { name: 'message.list', element: ui.message.list },
            { name: 'message.form', element: ui.message.form },
        ];

        for (const { name, element } of criticalElements) {
            if (!element) {
                console.error(`❌ Elemento crítico não encontrado: ${name}`);
                return false;
            }
        }
        return true;
    }

    // --- CORREÇÃO DO CSS DINÂMICO ---
    function fixMessageAreaLayout() {
        if (!ui.message.area || !ui.message.list) return;
        
        try {
            ui.message.list.style.position = 'relative';
            ui.message.list.style.inset = 'auto';
            ui.message.list.style.height = 'auto';
            ui.message.list.style.overflowY = 'auto';
            
            ui.message.area.style.display = 'flex';
            ui.message.area.style.flexDirection = 'column';
            ui.message.area.style.flex = '1';
            ui.message.area.style.minHeight = '0';
            ui.message.area.style.overflow = 'hidden';
            
            ui.message.list.style.flex = '1';
            ui.message.list.style.overflowY = 'auto';
            ui.message.list.style.padding = '1rem';
            ui.message.list.style.paddingBottom = '2rem';
        } catch (error) {
            console.warn('⚠️ Erro ao ajustar layout da área de mensagens:', error);
        }
    }

    // --- API & HELPERS ---
    async function apiFetch(url, options = {}) {
        if (!state.currentUser.csrfToken) {
            console.warn('CSRF token não disponível');
            return null;
        }

        const defaultHeaders = {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': state.currentUser.csrfToken,
        };
        
        if (!(options.body instanceof FormData)) {
            defaultHeaders['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers: { ...defaultHeaders, ...options.headers },
            });

            // Verifica se a resposta é JSON válido
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Resposta não é JSON válido');
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || errorData.error || `HTTP error! status: ${response.status}`);
            }

            return response.status === 204 ? null : response.json();
        } catch (error) {
            console.error('API Fetch Error:', error);
            throw error;
        }
    }

    function formatTime(timestamp) {
        if (!timestamp) return '';
        try {
            return new Date(timestamp).toLocaleTimeString('pt-BR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } catch (error) {
            return '';
        }
    }

    function formatDateSeparator(date) {
        try {
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);

            if (date.toDateString() === today.toDateString()) {
                return 'Hoje';
            }
            if (date.toDateString() === yesterday.toDateString()) {
                return 'Ontem';
            }
            return date.toLocaleDateString('pt-BR', { 
                day: '2-digit', 
                month: 'long', 
                year: 'numeric' 
            });
        } catch (error) {
            return '';
        }
    }

    function scrollToBottom() {
        if (ui.message.area) {
            setTimeout(() => {
                ui.message.area.scrollTop = ui.message.area.scrollHeight;
            }, 100);
        }
    }

    // --- TOAST NOTIFICATIONS ---
    function showToast(message, type = 'info') {
        if (!ui.toastContainer) return;

        const toastConfig = {
            success: { icon: 'fa-check-circle', color: 'text-green-500' },
            error: { icon: 'fa-times-circle', color: 'text-red-500' },
            info: { icon: 'fa-info-circle', color: 'text-blue-500' },
            warning: { icon: 'fa-exclamation-triangle', color: 'text-yellow-500' },
        };
        const config = toastConfig[type];

        try {
            const toastNode = ui.templates.toast.content.cloneNode(true);
            const toastIcon = toastNode.querySelector('.toast-icon');
            if (toastIcon) {
                toastIcon.innerHTML = `<i class="fas ${config.icon} ${config.color}"></i>`;
            }
            const textElement = toastNode.querySelector('.pl-4');
            if (textElement) {
                textElement.textContent = message;
            }
            
            const toastElement = toastNode.firstElementChild;
            if (toastElement) {
                ui.toastContainer.appendChild(toastElement);
                
                setTimeout(() => {
                    toastElement.classList.add('opacity-0', 'transform', 'translate-x-full');
                    setTimeout(() => {
                        if (toastElement.parentNode) {
                            toastElement.remove();
                        }
                    }, 500);
                }, 4000);
            }
        } catch (error) {
            console.error('Erro ao mostrar toast:', error);
        }
    }

    // --- MODAL FUNCTIONS ---
    function showModal(modalId) {
        try {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Erro ao mostrar modal:', error);
        }
    }

    function hideModal(modalId) {
        try {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('hidden');
            }
        } catch (error) {
            console.error('Erro ao esconder modal:', error);
        }
    }

    // --- SISTEMA DE EXCLUSÃO ---
    function initializeDeleteSystem() {
        console.log('🔧 Inicializando sistema de exclusão...');
        
        try {
            const confirmDeleteMessage = document.getElementById('confirmDeleteMessage');
            const confirmDeleteConversation = document.getElementById('confirmDeleteConversation');
            
            if (confirmDeleteMessage) {
                confirmDeleteMessage.addEventListener('click', deleteMessage);
            }
            if (confirmDeleteConversation) {
                confirmDeleteConversation.addEventListener('click', deleteConversation);
            }
        } catch (error) {
            console.error('Erro ao inicializar sistema de exclusão:', error);
        }
    }

    function prepareMessageDeletion(messageId, messageElement) {
        state.currentMessageToDelete = { id: messageId, element: messageElement };
        showModal('deleteMessageModal');
    }

    function prepareConversationDeletion(conversationId) {
        state.currentConversationToDelete = { id: conversationId };
        showModal('deleteConversationModal');
    }

    async function deleteMessage() {
        if (!state.currentMessageToDelete || !state.activeConversationId) {
            showToast('❌ Erro: Conversa não selecionada', 'error');
            return;
        }
        
        try {
            const response = await apiFetch(
                `/api/chat/conversations/${state.activeConversationId}/messages/${state.currentMessageToDelete.id}/delete-message/`,
                { method: 'DELETE' }
            );
            
            if (response && response.status === 'mensagem excluída') {
                if (state.currentMessageToDelete.element) {
                    state.currentMessageToDelete.element.remove();
                }
                showToast('✅ Mensagem excluída com sucesso', 'success');
            } else {
                showToast('❌ Erro ao excluir mensagem', 'error');
            }
        } catch (error) {
            console.error('Erro ao excluir mensagem:', error);
            showToast('❌ Erro de conexão ao excluir mensagem', 'error');
        } finally {
            hideModal('deleteMessageModal');
            state.currentMessageToDelete = null;
        }
    }

    async function deleteConversation() {
        if (!state.currentConversationToDelete) {
            showToast('❌ Erro: Conversa não selecionada', 'error');
            return;
        }
        
        try {
            const response = await apiFetch(
                `/api/chat/conversations/${state.currentConversationToDelete.id}/delete-conversation/`,
                { method: 'DELETE' }
            );
            
            if (response && response.status === 'conversa excluída') {
                showToast('✅ Conversa excluída com sucesso', 'success');
                
                const conversationElement = document.querySelector(`[data-conversation-id="${state.currentConversationToDelete.id}"]`);
                if (conversationElement) {
                    conversationElement.remove();
                }
                
                showNoConversationSelected();
                fetchAndRenderConversations();
            } else {
                showToast('❌ Erro ao excluir conversa', 'error');
            }
        } catch (error) {
            console.error('Erro ao excluir conversa:', error);
            showToast('❌ Erro de conexão ao excluir conversa', 'error');
        } finally {
            hideModal('deleteConversationModal');
            state.currentConversationToDelete = null;
        }
    }

    // --- DROPDOWN MANAGEMENT ---
    function initializeDropdownSystem() {
        console.log('🔧 Inicializando sistema de dropdowns...');
        
        // Fechar dropdown quando clicar fora
        document.addEventListener('click', function(e) {
            if (state.activeDropdown && 
                !e.target.closest('.conversation-menu-btn') && 
                !e.target.closest('.message-menu-btn') && 
                !e.target.closest('.actions-dropdown')) {
                state.activeDropdown.classList.add('hidden');
                state.activeDropdown = null;
            }
        });

        // Toggle dropdown das conversas
        document.addEventListener('click', function(e) {
            if (e.target.closest('.conversation-menu-btn')) {
                e.stopPropagation();
                const btn = e.target.closest('.conversation-menu-btn');
                const dropdown = btn.parentElement.querySelector('.conversation-dropdown');
                
                if (!dropdown) return;
                
                // Fecha dropdown anterior se existir
                if (state.activeDropdown && state.activeDropdown !== dropdown) {
                    state.activeDropdown.classList.add('hidden');
                }
                
                // Toggle dropdown atual
                dropdown.classList.toggle('hidden');
                state.activeDropdown = dropdown.classList.contains('hidden') ? null : dropdown;
            }
        });

        // Toggle dropdown das mensagens
        document.addEventListener('click', function(e) {
            if (e.target.closest('.message-menu-btn')) {
                e.stopPropagation();
                const btn = e.target.closest('.message-menu-btn');
                const dropdown = btn.parentElement.querySelector('.message-dropdown');
                
                if (!dropdown) return;
                
                // Fecha dropdown anterior se existir
                if (state.activeDropdown && state.activeDropdown !== dropdown) {
                    state.activeDropdown.classList.add('hidden');
                }
                
                // Toggle dropdown atual
                dropdown.classList.toggle('hidden');
                state.activeDropdown = dropdown.classList.contains('hidden') ? null : dropdown;
            }
        });

        // Ações dos dropdowns
        document.addEventListener('click', function(e) {
            // Excluir conversa
            if (e.target.closest('.delete-conversation-btn')) {
                e.stopPropagation();
                const conversationItem = e.target.closest('.conversation-item');
                const conversationId = conversationItem?.dataset.conversationId;
                if (conversationId) {
                    prepareConversationDeletion(conversationId);
                }
                if (state.activeDropdown) {
                    state.activeDropdown.classList.add('hidden');
                    state.activeDropdown = null;
                }
            }

            // Excluir mensagem
            if (e.target.closest('.delete-message-btn')) {
                e.stopPropagation();
                const messageElement = e.target.closest('.flex.justify-end, .flex.justify-start');
                const messageId = messageElement?.dataset.messageId;
                if (messageId) {
                    prepareMessageDeletion(messageId, messageElement);
                }
                if (state.activeDropdown) {
                    state.activeDropdown.classList.add('hidden');
                    state.activeDropdown = null;
                }
            }

            // Copiar mensagem
            if (e.target.closest('.copy-message-btn')) {
                e.stopPropagation();
                const messageElement = e.target.closest('.flex.justify-end, .flex.justify-start');
                const messageText = messageElement?.querySelector('.message-text')?.textContent;
                if (messageText) {
                    navigator.clipboard.writeText(messageText).then(() => {
                        showToast('📋 Mensagem copiada!', 'success');
                    }).catch(() => {
                        showToast('❌ Erro ao copiar mensagem', 'error');
                    });
                }
                if (state.activeDropdown) {
                    state.activeDropdown.classList.add('hidden');
                    state.activeDropdown = null;
                }
            }
        });
    }

    // --- SIDEBAR LOGIC ---
    function switchTab(tabName) {
        state.activeTab = tabName;
        
        if (ui.sidebar.tabs) {
            ui.sidebar.tabs.forEach(tab => {
                if (!tab) return;
                const isSelected = tab.dataset.tab === tabName;
                tab.classList.toggle('text-blue-500', isSelected);
                tab.classList.toggle('border-blue-500', isSelected);
                tab.classList.toggle('text-gray-500', !isSelected);
                tab.classList.toggle('border-transparent', !isSelected);
            });
        }

        ['conversation', 'group', 'contact'].forEach(type => {
            const container = document.getElementById(`${type}-list-container`);
            if (container) {
                container.classList.toggle('hidden', type !== tabName.slice(0, -1));
            }
        });

        switch (tabName) {
            case 'conversations':
                fetchAndRenderConversations();
                break;
            case 'groups':
                fetchAndRenderGroups();
                break;
            case 'contacts':
                fetchAndRenderContacts();
                break;
        }
    }

    function startNewConversation() {
        switchTab('contacts');
    }

    function renderPlaceholder(container, icon, text) {
        if (!container) return;
        try {
            const placeholder = ui.templates.placeholder.content.cloneNode(true);
            const iconEl = placeholder.querySelector('.placeholder-icon');
            if(iconEl) iconEl.className = `placeholder-icon ${icon} text-4xl mb-3`;
            const textEl = placeholder.querySelector('.placeholder-text');
            if(textEl) textEl.textContent = text;
            container.innerHTML = '';
            container.appendChild(placeholder);
        } catch (error) {
            console.error('Erro ao renderizar placeholder:', error);
        }
    }

    // --- CONVERSATIONS ---
    async function createOrOpenPrivateConversation(userId) {
        try {
            const conversation = await apiFetch('/api/chat/conversations/create_or_open/', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId }),
            });
            await fetchAndRenderConversations();
            switchTab('conversations');
            selectConversation(conversation.id);
        } catch (e) {
            showToast(e.message, 'error');
        }
    }

    async function fetchAndRenderConversations() {
        if (!ui.sidebar.conversationList) return;
        renderPlaceholder(ui.sidebar.conversationList, 'fas fa-spinner fa-spin', 'Carregando conversas...');
        try {
            const response = await apiFetch('/api/chat/conversations/');
            
            let conversations = [];
            if (Array.isArray(response)) {
                conversations = response;
            } else if (response && response.results) {
                conversations = response.results;
            } else if (response && typeof response === 'object') {
                conversations = [response];
            }
            
            state.conversations.clear();
            conversations.forEach(c => state.conversations.set(c.id, c));
            renderConversationList(conversations);
        } catch (e) {
            console.error('Erro ao carregar conversas:', e);
            renderPlaceholder(ui.sidebar.conversationList, 'fas fa-exclamation-circle', 'Erro ao carregar conversas.');
        }
    }

    function renderConversationList(convs) {
        const container = ui.sidebar.conversationList;
        if (!container) return;
        
        try {
            if (convs.length === 0) {
                renderPlaceholder(container, 'fas fa-comments', 'Nenhuma conversa encontrada.');
                return;
            }
            
            container.innerHTML = '';
            convs.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)).forEach(conv => {
                const item = ui.templates.conversation.content.cloneNode(true);
                const other = conv.participants?.find(p => p.user.id != state.currentUser.id);
                const name = conv.is_group ? conv.name : other?.user.display_name || 'Conversa';
                
                const convItem = item.querySelector('.conversation-item');
                if (!convItem) return;
                
                convItem.dataset.conversationId = conv.id;
                if (conv.id === state.activeConversationId) {
                    convItem.classList.add('active');
                }

                const avatarImg = item.querySelector('.avatar-img');
                const avatarPlaceholder = item.querySelector('.avatar-placeholder');
                const userForAvatar = conv.is_group ? null : other?.user;

                if (userForAvatar && userForAvatar.image_url) {
                    if(avatarImg) {
                        avatarImg.src = userForAvatar.image_url;
                        avatarImg.classList.remove('hidden');
                    }
                    if(avatarPlaceholder) avatarPlaceholder.remove();
                } else {
                    if(avatarPlaceholder) avatarPlaceholder.textContent = name.charAt(0).toUpperCase();
                    if(avatarImg) avatarImg.remove();
                }

                const h4 = item.querySelector('h4');
                if(h4) h4.textContent = name;
                const lastMessage = item.querySelector('.last-message');
                if(lastMessage) lastMessage.textContent = conv.last_message?.text?.substring(0, 50) + '...' || 'Nenhuma mensagem';
                const time = item.querySelector('.time');
                if(time) time.textContent = conv.last_message ? formatTime(conv.last_message.created_at) : '';
                
                const unread = item.querySelector('.unread-count');
                if (unread) {
                    if (conv.unread_count > 0) {
                        unread.textContent = conv.unread_count;
                    } else {
                        unread.remove();
                    }
                }

                convItem.addEventListener('click', (e) => {
                    if (!e.target.closest('.conversation-actions')) {
                        selectConversation(conv.id);
                    }
                });
                
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Erro ao renderizar lista de conversas:', error);
            renderPlaceholder(container, 'fas fa-exclamation-circle', 'Erro ao carregar conversas.');
        }
    }

    // --- CONTACTS ---
    async function fetchAndRenderContacts() {
        if (!ui.sidebar.contactList) return;
        renderPlaceholder(ui.sidebar.contactList, 'fas fa-spinner fa-spin', 'Carregando contatos...');
        try {
            const response = await apiFetch('/api/chat/users/');
            const users = Array.isArray(response) ? response : (response.results || []);
            const filteredUsers = users.filter(u => u.id != state.currentUser.id);
            
            const presences = await apiFetch(`/api/chat/presence/?user_ids=${filteredUsers.map(u => u.id).join(',')}`);
            state.contacts = filteredUsers.map(u => ({ 
                ...u, 
                presence: presences?.[u.id] || { status: 'offline' } 
            }));
            renderContactList(state.contacts);
        } catch (e) {
            console.error('Erro ao carregar contatos:', e);
            renderPlaceholder(ui.sidebar.contactList, 'fas fa-user-times', 'Erro ao carregar contatos.');
        }
    }

    function renderContactList(contacts) {
        const container = ui.sidebar.contactList;
        if (!container) return;
        
        try {
            if (contacts.length === 0) {
                renderPlaceholder(container, 'fas fa-users-slash', 'Nenhum contato encontrado.');
                return;
            }
            
            container.innerHTML = '';
            contacts.forEach(c => {
                const item = ui.templates.contact.content.cloneNode(true);
                const contactItem = item.querySelector('.contact-item');
                const name = c.display_name || c.email;

                const avatarImg = item.querySelector('.avatar-img');
                const avatarPlaceholder = item.querySelector('.avatar-placeholder');
                if (c.image_url) {
                    if(avatarImg) {
                        avatarImg.src = c.image_url;
                        avatarImg.classList.remove('hidden');
                    }
                    if(avatarPlaceholder) avatarPlaceholder.remove();
                } else {
                    if(avatarPlaceholder) avatarPlaceholder.textContent = name.charAt(0).toUpperCase();
                    if(avatarImg) avatarImg.remove();
                }

                const h4 = item.querySelector('h4');
                if(h4) h4.textContent = name;
                const statusText = item.querySelector('.status-text');
                if(statusText) statusText.textContent = c.presence.status;
                const statusIndicator = item.querySelector('.status-indicator');
                if(statusIndicator) {
                    statusIndicator.classList.add(c.presence.status === 'online' ? 'bg-green-500' : 'bg-gray-400');
                    statusIndicator.classList.add('border-white', 'dark:border-gray-900');
                }
                
                if(contactItem) {
                    contactItem.addEventListener('click', () => createOrOpenPrivateConversation(c.id));
                }
                
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Erro ao renderizar lista de contatos:', error);
            renderPlaceholder(container, 'fas fa-user-times', 'Erro ao carregar contatos.');
        }
    }

    // --- GROUPS ---
    async function fetchAndRenderGroups() {
        if (!ui.sidebar.groupList) return;
        renderPlaceholder(ui.sidebar.groupList, 'fas fa-spinner fa-spin', 'Carregando grupos...');
        try {
            const response = await apiFetch('/api/chat/groups/');
            state.groups = Array.isArray(response) ? response : (response.results || []);
            renderGroupList(state.groups);
        } catch (e) {
            console.error('Erro ao carregar grupos:', e);
            renderPlaceholder(ui.sidebar.groupList, 'fas fa-exclamation-circle', 'Erro ao carregar grupos.');
        }
    }

    function renderGroupList(groups) {
        const container = ui.sidebar.groupList;
        if (!container) return;
        
        try {
            if (groups.length === 0) {
                renderPlaceholder(container, 'fas fa-users', 'Nenhum grupo disponível.');
                return;
            }
            
            container.innerHTML = '';
            groups.forEach(g => {
                const item = ui.templates.group.content.cloneNode(true);
                const h4 = item.querySelector('h4');
                if(h4) h4.textContent = g.name;
                const members = item.querySelector('.members-count');
                if(members) members.textContent = `${g.participants_count || g.participants?.length || 0} membros`;
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Erro ao renderizar lista de grupos:', error);
            renderPlaceholder(container, 'fas fa-exclamation-circle', 'Erro ao carregar grupos.');
        }
    }

    // --- USER INFO MODAL ---
    function hideInfoModal() {
        const modal = ui.infoModal.container;
        if(modal) {
            const transformEl = modal.querySelector('.transform');
            if(transformEl) transformEl.classList.add('scale-95', 'opacity-0');
            setTimeout(() => modal.classList.add('hidden'), 300);
        }
    }

    async function showInfoModal(userId) {
        const modal = ui.infoModal.container;
        if(!modal) return;
        
        try {
            modal.classList.remove('hidden');
            const transformEl = modal.querySelector('.transform');
            if(transformEl) setTimeout(() => transformEl.classList.remove('scale-95', 'opacity-0'), 10);

            if(ui.infoModal.loading) ui.infoModal.loading.classList.remove('hidden');
            if(ui.infoModal.data) ui.infoModal.data.classList.add('hidden');

            const profile = await apiFetch(`/api/chat/users/${userId}/profile/`);

            const nomeDeGuerra = profile.nome_de_guerra || 'N/A';
            const postoGrad = profile.promocao?.posto_grad || '';
            const sgb = profile.situacao?.sgb || '';
            const re = profile.cadastro?.re || 'N/A';
            const dig = profile.cadastro?.dig || '';
            const nomeCompleto = profile.full_name || 'N/A';
            const secao = profile.situacao?.funcao || 'N/A';
            const imageUrl = profile.avatar;

            if(ui.infoModal.name) ui.infoModal.name.textContent = nomeDeGuerra;
            if(ui.infoModal.posto) ui.infoModal.posto.textContent = postoGrad;
            if(ui.infoModal.sgbDisplay) ui.infoModal.sgbDisplay.textContent = sgb ? `SGB: ${sgb}` : '';
            if(ui.infoModal.re) ui.infoModal.re.textContent = (re && dig) ? `${re}-${dig}` : re;
            if(ui.infoModal.nomeCompleto) ui.infoModal.nomeCompleto.textContent = nomeCompleto;
            if(ui.infoModal.sgb) ui.infoModal.sgb.textContent = sgb || 'N/A';
            if(ui.infoModal.secao) ui.infoModal.secao.textContent = secao;

            if (imageUrl) {
                if(ui.infoModal.img) {
                    ui.infoModal.img.src = imageUrl;
                    ui.infoModal.img.classList.remove('hidden');
                }
                if(ui.infoModal.avatarPlaceholder) ui.infoModal.avatarPlaceholder.classList.add('hidden');
            } else {
                if(ui.infoModal.avatarInitial) ui.infoModal.avatarInitial.textContent = (nomeDeGuerra || ' ').charAt(0).toUpperCase();
                if(ui.infoModal.img) ui.infoModal.img.classList.add('hidden');
                if(ui.infoModal.avatarPlaceholder) ui.infoModal.avatarPlaceholder.classList.remove('hidden');
            }

            if(ui.infoModal.loading) ui.infoModal.loading.classList.add('hidden');
            if(ui.infoModal.data) ui.infoModal.data.classList.remove('hidden');

        } catch (e) {
            console.error('Erro ao carregar perfil:', e);
            showToast('Não foi possível carregar o perfil.', 'error');
            hideInfoModal();
        }
    }

    // --- ACTIVE CONVERSATION ---
    function selectConversation(conversationId) {
        if (state.activeConversationId === conversationId && ui.activeConversation.container && !ui.activeConversation.container.classList.contains('hidden')) return;
        
        state.activeConversationId = conversationId;
        renderConversationList(Array.from(state.conversations.values()));
        const conv = state.conversations.get(conversationId);
        if (!conv) return;

        fixMessageAreaLayout();

        if(ui.initialScreen) ui.initialScreen.classList.add('hidden');
        if(ui.activeConversation.container) {
            ui.activeConversation.container.classList.remove('hidden');
        }

        const other = conv.participants?.find(p => p.user.id != state.currentUser.id);
        const name = conv.is_group ? conv.name : other?.user.display_name || 'Conversa';
        if(ui.activeConversation.name) ui.activeConversation.name.textContent = name;
        if(ui.activeConversation.avatar) ui.activeConversation.avatar.textContent = name.charAt(0).toUpperCase();
        
        if(ui.activeConversation.status && other?.user.presence) {
            const status = other.user.presence.status || 'offline';
            ui.activeConversation.status.className = `absolute bottom-0 right-0 w-2.5 h-2.5 border-2 rounded-full border-white dark:border-gray-800 ${status === 'online' ? 'bg-green-500' : 'bg-gray-400'}`;
        }

        if (!conv.is_group && other && ui.activeConversation.infoBtn) {
            ui.activeConversation.infoBtn.onclick = () => showInfoModal(other.user.id);
            ui.activeConversation.infoBtn.classList.remove('hidden');
        } else if (ui.activeConversation.infoBtn) {
            ui.activeConversation.infoBtn.classList.add('hidden');
        }

        fetchMessages(conversationId);
        connectWebSocket(conversationId);
    }

    function showNoConversationSelected() {
        state.activeConversationId = null;
        if(ui.initialScreen) {
            ui.initialScreen.classList.remove('hidden');
        }
        if(ui.activeConversation.container) {
            ui.activeConversation.container.classList.add('hidden');
        }
        
        if (state.socket) {
            state.socket.close();
            state.socket = null;
        }
    }

    function showConversationsSidebar() {
        showNoConversationSelected();
    }

    // --- MESSAGES ---
    async function fetchMessages(conversationId) {
        if(ui.message.list) {
            ui.message.list.innerHTML = '';
            ui.message.list.style.padding = '1rem';
            ui.message.list.style.paddingBottom = '2rem';
        }
        state.lastMessageDate = null;
        try {
            const response = await apiFetch(`/api/chat/conversations/${conversationId}/messages/`);
            const messages = Array.isArray(response) ? response : (response.results || []);
            messages.reverse().forEach(m => appendMessage(m, false));
            setTimeout(scrollToBottom, 100);
        } catch (e) {
            console.error('Erro ao carregar mensagens:', e);
            showToast('Erro ao carregar mensagens', 'error');
        }
    }

    function appendMessage(message, animate = true) {
        if (!message || !message.sender) {
            console.error('Mensagem inválida:', message);
            return;
        }

        try {
            const messageDate = new Date(message.created_at);
            
            if (!state.lastMessageDate || messageDate.toDateString() !== state.lastMessageDate.toDateString()) {
                const separator = ui.templates.dateSeparator.content.cloneNode(true);
                const separatorSpan = separator.querySelector('span');
                if (separatorSpan) {
                    separatorSpan.textContent = formatDateSeparator(messageDate);
                }
                if (ui.message.list) {
                    ui.message.list.appendChild(separator);
                }
            }
            state.lastMessageDate = messageDate;

            const isOwn = message.sender.id == state.currentUser.id;
            const templateId = isOwn ? 'message-sent-template' : 'message-received-template';
            const template = document.getElementById(templateId);

            if (!template) {
                console.error(`Template não encontrado: #${templateId}`);
                return;
            }

            const item = template.content.cloneNode(true);
            const messageElement = item.firstElementChild;
            if (!messageElement) return;

            messageElement.dataset.messageId = message.id;

            const senderNameEl = messageElement.querySelector('.sender-name');
            const messageTextEl = messageElement.querySelector('.message-text');
            const userAvatarEl = messageElement.querySelector('.user-avatar');
            const timestampEl = messageElement.querySelector('.timestamp');
            const readStatusEl = messageElement.querySelector('.read-status');

            if (messageTextEl) messageTextEl.textContent = message.decrypted_text || message.text || '';
            if (timestampEl) timestampEl.textContent = formatTime(message.created_at);

            // Avatar
            const setupAvatar = (element, imageUrl, initial) => {
                if (!element) return;
                if (imageUrl) {
                    element.innerHTML = `<img src="${imageUrl}" class="w-full h-full rounded-full object-cover" alt="Avatar">`;
                } else {
                    element.innerHTML = `<span>${initial}</span>`;
                    element.classList.add('bg-gradient-to-br', 'from-gray-500', 'to-gray-600');
                }
            };

            if (isOwn) {
                const initial = (state.currentUser.username || 'V').charAt(0).toUpperCase();
                setupAvatar(userAvatarEl, state.currentUser.imageUrl, initial);
                
                if (readStatusEl) {
                    let statusIcon = '';
                    switch (message.status) {
                        case 'sent': statusIcon = '<i class="fas fa-check text-gray-400"></i>'; break;
                        case 'delivered': statusIcon = '<i class="fas fa-check-double text-gray-400"></i>'; break;
                        case 'read': statusIcon = '<i class="fas fa-check-double text-blue-400"></i>'; break;
                        default: statusIcon = '<i class="far fa-clock text-gray-400"></i>';
                    }
                    readStatusEl.innerHTML = statusIcon;
                }
            } else {
                const senderDisplayName = message.sender.display_name || 'Usuário';
                const initial = senderDisplayName.charAt(0).toUpperCase();
                if (senderNameEl) senderNameEl.textContent = senderDisplayName;
                setupAvatar(userAvatarEl, message.sender.image_url, initial);
            }

            if (ui.message.list) {
                if (animate) {
                    messageElement.classList.add('opacity-0');
                    setTimeout(() => messageElement.classList.remove('opacity-0'), 10);
                }
                ui.message.list.appendChild(messageElement);
                if (animate) {
                    setTimeout(scrollToBottom, 50);
                }
            }
        } catch (error) {
            console.error('Erro ao adicionar mensagem:', error);
        }
    }

    async function handleSendMessage(e) {
        e.preventDefault();
        if (!ui.message.input || !state.activeConversationId) return;
        const text = ui.message.input.value.trim();
        if (!text && !state.selectedFile) return;

        try {
            if (state.selectedFile) {
                const formData = new FormData();
                if(text) formData.append('text', text);
                formData.append('attachment', state.selectedFile);
                await apiFetch(`/api/chat/conversations/${state.activeConversationId}/messages/`, {
                    method: 'POST',
                    body: formData,
                });
                removeSelectedFile();
            } else if (state.socket && state.socket.readyState === WebSocket.OPEN) {
                state.socket.send(JSON.stringify({ type: 'message.send', text }));
            } else {
                await apiFetch(`/api/chat/conversations/${state.activeConversationId}/messages/`, {
                    method: 'POST',
                    body: JSON.stringify({ text: text })
                });
            }
            ui.message.input.value = '';
        } catch (e) {
            console.error('Erro ao enviar mensagem:', e);
            showToast('Erro ao enviar mensagem', 'error');
        }
    }

    // --- FILE HANDLING ---
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            showToast('O arquivo não pode exceder 5 MB.', 'error');
            return;
        }
        state.selectedFile = file;
        if(ui.filePreview.name) ui.filePreview.name.textContent = file.name;
        if(ui.filePreview.container) ui.filePreview.container.classList.remove('hidden');
    }

    function removeSelectedFile() {
        state.selectedFile = null;
        if(ui.message.fileInput) ui.message.fileInput.value = '';
        if(ui.filePreview.container) ui.filePreview.container.classList.add('hidden');
    }

    // --- WEBSOCKET ---
// CORREÇÃO: Função connectWebSocket melhorada
function connectWebSocket(conversationId) {
    // Fecha conexão anterior se existir
    if (state.socket) {
        state.socket.close();
        state.socket = null;
    }

    // Limpa timer de reconexão anterior
    if (state.reconnect.timer) {
        clearTimeout(state.reconnect.timer);
        state.reconnect.timer = null;
    }

    try {
        // Determina o protocolo WebSocket baseado no protocolo HTTP
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        
        // Constrói a URL do WebSocket
        let wsUrl;
        if (window.location.port) {
            wsUrl = `${protocol}//${window.location.hostname}:${window.location.port}/ws/chat/${conversationId}/`;
        } else {
            wsUrl = `${protocol}//${window.location.hostname}/ws/chat/${conversationId}/`;
        }

        console.log(`🔗 Conectando WebSocket: ${wsUrl}`);
        
        state.socket = new WebSocket(wsUrl);

        state.socket.onopen = () => {
            console.log('✅ WebSocket conectado com sucesso');
            state.reconnect.attempts = 0;
            
            // Notifica que está online
            if (state.socket.readyState === WebSocket.OPEN) {
                state.socket.send(JSON.stringify({ 
                    type: 'presence.update', 
                    status: 'online' 
                }));
            }
        };

        state.socket.onclose = (event) => {
            console.log('🔌 WebSocket desconectado:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            
            // Não tenta reconectar se foi um fechamento limpo
            if (event.code === 1000) {
                console.log('ℹ️ Conexão fechada normalmente');
                return;
            }
            
            // Tentar reconectar apenas se ainda estiver na mesma conversa
            if (state.activeConversationId === conversationId) {
                attemptReconnect(conversationId);
            }
        };

        state.socket.onerror = (error) => {
            console.error('❌ Erro no WebSocket:', error);
        };

        state.socket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('❌ Erro ao processar mensagem WebSocket:', error, e.data);
            }
        };

    } catch (error) {
        console.error('❌ Erro fatal ao conectar WebSocket:', error);
        showToast('❌ Erro de conexão com o chat', 'error');
    }
}

// Função melhorada de reconexão
function attemptReconnect(conversationId) {
    if (state.reconnect.attempts >= state.reconnect.maxAttempts) {
        console.error('❌ Máximo de tentativas de reconexão atingido');
        showToast('❌ Conexão perdida. Recarregue a página para reconectar.', 'error');
        return;
    }

    state.reconnect.attempts++;
    const delay = Math.min(state.reconnect.delay * state.reconnect.attempts, 10000); // Max 10 segundos
    
    console.log(`🔄 Tentativa ${state.reconnect.attempts} de reconexão em ${delay}ms`);
    
    state.reconnect.timer = setTimeout(() => {
        // Verifica se ainda estamos na mesma conversa antes de reconectar
        if (state.activeConversationId === conversationId) {
            console.log(`🔄 Executando reconexão para conversa: ${conversationId}`);
            connectWebSocket(conversationId);
        } else {
            console.log('ℹ️ Não reconectando - conversa mudou');
        }
    }, delay);
}

    function handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message.receive':
                if (data.message.conversation.id === state.activeConversationId) {
                    appendMessage(data.message);
                }
                fetchAndRenderConversations();
                break;
            case 'typing.indicator':
                if (data.user_id !== state.currentUser.id && ui.typingIndicator.container && ui.typingIndicator.user) {
                    if (data.action === 'start') {
                        ui.typingIndicator.user.textContent = data.user_name;
                        ui.typingIndicator.container.classList.remove('hidden');
                    } else {
                        ui.typingIndicator.container.classList.add('hidden');
                    }
                }
                break;
            case 'presence.update':
                break;
            case 'message.delete':
                removeMessageFromUI(data.message_id);
                break;
        }
    }

    function attemptReconnect(conversationId) {
        if (state.reconnect.attempts < state.reconnect.maxAttempts) {
            state.reconnect.attempts++;
            const delay = state.reconnect.delay * state.reconnect.attempts;
            
            console.log(`🔄 Tentativa ${state.reconnect.attempts} de reconexão em ${delay}ms`);
            
            state.reconnect.timer = setTimeout(() => {
                if (state.activeConversationId === conversationId) {
                    connectWebSocket(conversationId);
                }
            }, delay);
        } else {
            console.error('❌ Máximo de tentativas de reconexão atingido');
            showToast('❌ Conexão perdida. Recarregue a página.', 'error');
        }
    }

    function removeMessageFromUI(messageId) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            messageElement.remove();
        }
    }

    // --- CELERY TASK MANAGEMENT ---
    function initializeCeleryTasks() {
        console.log('🔧 Inicializando gerenciamento de tarefas Celery...');
        setInterval(checkCeleryStatus, 30000);
    }

    async function checkCeleryStatus() {
        try {
            const response = await apiFetch('/api/chat/admin/stats/');
            if (response) {
                console.log('✅ Celery está funcionando');
            }
        } catch (error) {
            console.warn('⚠️ Não foi possível verificar status do Celery');
        }
    }

    // --- EVENT LISTENERS ---
    function setupEventListeners() {
        try {
            if(ui.sidebar.newConversationBtn) {
                ui.sidebar.newConversationBtn.addEventListener('click', startNewConversation);
            }
            
            if(ui.sidebar.tabs) {
                ui.sidebar.tabs.forEach(tab => {
                    if (tab) {
                        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
                    }
                });
            }
            
            if(ui.activeConversation.backBtn) {
                ui.activeConversation.backBtn.addEventListener('click', showConversationsSidebar);
            }
            
            if(ui.message.form) {
                ui.message.form.addEventListener('submit', handleSendMessage);
            }
            
            if(ui.message.attachFileBtn && ui.message.fileInput) {
                ui.message.attachFileBtn.addEventListener('click', () => ui.message.fileInput.click());
            }
            
            if(ui.message.fileInput) {
                ui.message.fileInput.addEventListener('change', handleFileSelect);
            }
            
            if(ui.filePreview.removeBtn) {
                ui.filePreview.removeBtn.addEventListener('click', removeSelectedFile);
            }
            
            if(ui.infoModal.closeBtn) {
                ui.infoModal.closeBtn.addEventListener('click', hideInfoModal);
            }
            
            if(ui.infoModal.container) {
                ui.infoModal.container.addEventListener('click', (e) => {
                    if (e.target === ui.infoModal.container) hideInfoModal();
                });
            }

            if (ui.message.input) {
                ui.message.input.addEventListener('input', () => {
                    if (state.socket && state.socket.readyState === WebSocket.OPEN) {
                        if (!state.typingTimeout) {
                            state.socket.send(JSON.stringify({ type: 'typing.start' }));
                        }
                        clearTimeout(state.typingTimeout);
                        state.typingTimeout = setTimeout(() => {
                            state.socket.send(JSON.stringify({ type: 'typing.stop' }));
                            state.typingTimeout = null;
                        }, 2000);
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao configurar event listeners:', error);
        }
    }


    // VERIFICAÇÃO DE DEPENDÊNCIAS ANTES DE INICIALIZAR
function checkPrerequisites() {
    // Verifica se WebSocket está disponível
    if (!window.WebSocket) {
        console.error('❌ WebSocket não suportado neste navegador');
        showToast('Seu navegador não suporta WebSocket. Atualize para uma versão mais recente.', 'error');
        return false;
    }
    
    // Verifica se temos CSRF token
    if (!state.currentUser.csrfToken) {
        console.warn('⚠️ CSRF token não encontrado');
    }
    
    return true;
}

// Substitua a função init() original por:
function init() {
    console.log('🔧 Inicializando ChatApp...');
    
    if (!checkPrerequisites()) {
        return;
    }
    
    // Delay para garantir que o DOM está completamente carregado
    setTimeout(() => {
        if (!safeInit()) {
            console.warn('⚠️ Inicialização falhou - tentando novamente em 2s');
            setTimeout(init, 2000);
        }
    }, 500);
}

    // --- INICIALIZAÇÃO SEGURA ---
    function safeInit() {
        if (!validateCriticalElements()) {
            console.error('❌ Elementos críticos não encontrados - chat não pode ser inicializado');
            return false;
        }

        console.log('🚀 ChatApp inicializado com segurança');
        console.log('👤 Usuário carregado:', state.currentUser.username);
        
        fixMessageAreaLayout();
        setupEventListeners();
        initializeDeleteSystem();
        initializeDropdownSystem();
        initializeCeleryTasks();
        switchTab('conversations');
        
        return true;
    }

    // Inicialização principal
    function init() {
        console.log('🔧 Inicializando ChatApp...');
        
        // Delay para garantir que o DOM está completamente carregado
        setTimeout(() => {
            if (!safeInit()) {
                console.warn('⚠️ Inicialização falhou - tentando novamente em 1s');
                setTimeout(init, 1000);
            }
        }, 100);
    }

    // Inicia a aplicação
    init();
});