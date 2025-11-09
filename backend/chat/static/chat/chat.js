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
        main: document.querySelector('.flex-1.flex-col'), // Main chat area container
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
        // ADICIONE ESTA LINHA
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
            id: ui.chatContainer.dataset.userId,
            username: ui.chatContainer.dataset.username,
            imageUrl: ui.chatContainer.dataset.userImageUrl,
            csrfToken: ui.chatContainer.dataset.csrfToken,
        },
        socket: null,
        activeConversationId: null,
        activeTab: 'conversations', // conversations, groups, contacts
        conversations: new Map(),
        contacts: [],
        groups: [],
        typingTimeout: null,
        selectedFile: null,
        lastMessageDate: null,
        reconnect: { attempts: 0, maxAttempts: 5, delay: 1000 },
    };

    // --- API & HELPERS ---
    async function apiFetch(url, options = {}) {
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

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
                throw new Error(errorData.detail);
            }
            return response.status === 204 ? null : response.json();
        } catch (error) {
            console.error('API Fetch Error:', error);
            throw error;
        }
    }

    function formatTime(timestamp) {
        if (!timestamp) return '';
        return new Date(timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }

    function formatDateSeparator(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Hoje';
        }
        if (date.toDateString() === yesterday.toDateString()) {
            return 'Ontem';
        }
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
    }

    function scrollToBottom() {
        ui.message.area.scrollTop = ui.message.area.scrollHeight;
    }

    // --- TOAST NOTIFICATIONS ---
    function showToast(message, type = 'info') {
        const toastConfig = {
            success: { icon: 'fa-check-circle', color: 'text-green-500' },
            error: { icon: 'fa-times-circle', color: 'text-red-500' },
            info: { icon: 'fa-info-circle', color: 'text-blue-500' },
            warning: { icon: 'fa-exclamation-triangle', color: 'text-yellow-500' },
        };
        const config = toastConfig[type];

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
                setTimeout(() => toastElement.remove(), 500);
            }, 4000);
        }
    }

    // --- SIDEBAR LOGIC ---
    function switchTab(tabName) {
        state.activeTab = tabName;
        ui.sidebar.tabs.forEach(tab => {
            const isSelected = tab.dataset.tab === tabName;
            tab.classList.toggle('text-blue-500', isSelected);
            tab.classList.toggle('border-blue-500', isSelected);
            tab.classList.toggle('text-gray-500', !isSelected);
            tab.classList.toggle('dark:text-gray-400', !isSelected);
            tab.classList.toggle('border-transparent', !isSelected);
        });

        Object.values(ui.sidebar).forEach(el => {
            if (el.id && el.id.endsWith('-list-container')) {
                el.classList.add('hidden');
            }
        });

        const activeContainerId = `${tabName.slice(0, -1)}-list-container`;
        const activeContainer = document.getElementById(activeContainerId);
        if (activeContainer) {
            activeContainer.classList.remove('hidden');
        }

        switch (tabName) {
            case 'conversations': fetchAndRenderConversations(); break;
            case 'groups': fetchAndRenderGroups(); break;
            case 'contacts': fetchAndRenderContacts(); break;
        }
    }

    function startNewConversation() {
        switchTab('contacts');
    }

    function renderPlaceholder(container, icon, text) {
        if (!container) return;
        const placeholder = ui.templates.placeholder.content.cloneNode(true);
        const iconEl = placeholder.querySelector('.placeholder-icon');
        if(iconEl) iconEl.className = `placeholder-icon ${icon} text-4xl mb-3`;
        const textEl = placeholder.querySelector('.placeholder-text');
        if(textEl) textEl.textContent = text;
        container.innerHTML = '';
        container.appendChild(placeholder);
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
            const convs = (await apiFetch('/api/chat/conversations/')).results;
            state.conversations.clear();
            convs.forEach(c => state.conversations.set(c.id, c));
            renderConversationList(Array.from(state.conversations.values()));
        } catch (e) {
            showToast(e.message, 'error');
            renderPlaceholder(ui.sidebar.conversationList, 'fas fa-exclamation-circle', 'Erro ao carregar conversas.');
        }
    }

    function renderConversationList(convs) {
        const container = ui.sidebar.conversationList;
        if (!container) return;
        if (convs.length === 0) {
            renderPlaceholder(container, 'fas fa-comments', 'Nenhuma conversa encontrada.');
            return;
        }
        container.innerHTML = '';
        convs.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)).forEach(conv => {
            const item = ui.templates.conversation.content.cloneNode(true);
            const other = conv.participants.find(p => p.user.id != state.currentUser.id);
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
            if(lastMessage) lastMessage.textContent = conv.last_message?.text || 'Nenhuma mensagem';
            const time = item.querySelector('.time');
            if(time) time.textContent = conv.last_message ? formatTime(conv.last_message.created_at) : '';
            
            const unread = item.querySelector('.unread-count');
            if (unread) {
                if (conv.unread_count > 0) unread.textContent = conv.unread_count; else unread.remove();
            }

            convItem.addEventListener('click', () => selectConversation(conv.id));
            container.appendChild(item);
        });
    }

    // --- CONTACTS ---
    async function fetchAndRenderContacts() {
        if (!ui.sidebar.contactList) return;
        renderPlaceholder(ui.sidebar.contactList, 'fas fa-spinner fa-spin', 'Carregando contatos...');
        try {
            const users = (await apiFetch('/api/chat/users/')).results.filter(u => u.id != state.currentUser.id);
            const presences = await apiFetch(`/api/chat/presence/?user_ids=${users.map(u => u.id).join(',')}`);
            state.contacts = users.map(u => ({ ...u, presence: presences[u.id] || { status: 'offline' } }));
            renderContactList(state.contacts);
        } catch (e) {
            showToast(e.message, 'error');
            renderPlaceholder(ui.sidebar.contactList, 'fas fa-user-times', 'Erro ao carregar contatos.');
        }
    }

    function renderContactList(contacts) {
        const container = ui.sidebar.contactList;
        if (!container) return;
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
            
            if(contactItem) contactItem.addEventListener('click', () => createOrOpenPrivateConversation(c.id));
            
            container.appendChild(item);
        });
    }

    // --- GROUPS ---
    async function fetchAndRenderGroups() {
        if (!ui.sidebar.groupList) return;
        renderPlaceholder(ui.sidebar.groupList, 'fas fa-spinner fa-spin', 'Carregando grupos...');
        try {
            state.groups = (await apiFetch('/api/chat/groups/')).results;
            renderGroupList(state.groups);
        } catch (e) {
            showToast(e.message, 'error');
            renderPlaceholder(ui.sidebar.groupList, 'fas fa-exclamation-circle', 'Erro ao carregar grupos.');
        }
    }

    function renderGroupList(groups) {
        const container = ui.sidebar.groupList;
        if (!container) return;
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
            if(members) members.textContent = `${g.participants_count} membros`;
            container.appendChild(item);
        });
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
    modal.classList.remove('hidden');
    const transformEl = modal.querySelector('.transform');
    if(transformEl) setTimeout(() => transformEl.classList.remove('scale-95', 'opacity-0'), 10);

    if(ui.infoModal.loading) ui.infoModal.loading.classList.remove('hidden');
    if(ui.infoModal.data) ui.infoModal.data.classList.add('hidden');

    try {
        const profile = await apiFetch(`/api/chat/users/${userId}/profile/`);

        if(ui.infoModal.name) ui.infoModal.name.textContent = profile.nome_de_guerra || 'N/A';
        if(ui.infoModal.posto) ui.infoModal.posto.textContent = profile.posto_grad || 'N/A';
        
        // ADICIONE ESTAS LINHAS PARA EXIBIR O SGB NO CABEÇALHO
        if(ui.infoModal.sgbDisplay) {
            ui.infoModal.sgbDisplay.textContent = profile.sgb || 'N/A';
        }
        
        if(ui.infoModal.re) ui.infoModal.re.textContent = `${profile.re}-${profile.dig}` || 'N/A';
        if(ui.infoModal.nomeCompleto) ui.infoModal.nomeCompleto.textContent = profile.nome_completo || 'N/A';
        if(ui.infoModal.sgb) ui.infoModal.sgb.textContent = profile.sgb || 'N/A';
        if(ui.infoModal.secao) ui.infoModal.secao.textContent = profile.posto_secao || 'N/A';

        if (profile.image_url) {
            if(ui.infoModal.img) {
                ui.infoModal.img.src = profile.image_url;
                ui.infoModal.img.classList.remove('hidden');
            }
            if(ui.infoModal.avatarPlaceholder) ui.infoModal.avatarPlaceholder.classList.add('hidden');
        } else {
            if(ui.infoModal.avatarInitial) ui.infoModal.avatarInitial.textContent = (profile.nome_de_guerra || ' ').charAt(0).toUpperCase();
            if(ui.infoModal.img) ui.infoModal.img.classList.add('hidden');
            if(ui.infoModal.avatarPlaceholder) ui.infoModal.avatarPlaceholder.classList.remove('hidden');
        }

        if(ui.infoModal.loading) ui.infoModal.loading.classList.add('hidden');
        if(ui.infoModal.data) ui.infoModal.data.classList.remove('hidden');

    } catch (e) {
        showToast('Não foi possível carregar o perfil. Verifique se a API está configurada.', 'error');
        hideInfoModal();
    }
}

    // --- ACTIVE CONVERSATION ---
    function selectConversation(conversationId) {
        if (state.activeConversationId === conversationId && !ui.activeConversation.container.classList.contains('hidden')) return;
        
        state.activeConversationId = conversationId;
        renderConversationList(Array.from(state.conversations.values()));
        const conv = state.conversations.get(conversationId);
        if (!conv) return;

        if(ui.initialScreen) ui.initialScreen.style.display = 'none';
        if(ui.activeConversation.container) {
            ui.activeConversation.container.classList.remove('hidden');
            ui.activeConversation.container.classList.add('flex');
        }

        const other = conv.participants.find(p => p.user.id != state.currentUser.id);
        const name = conv.is_group ? conv.name : other?.user.display_name || 'Conversa';
        if(ui.activeConversation.name) ui.activeConversation.name.textContent = name;
        if(ui.activeConversation.avatar) ui.activeConversation.avatar.textContent = name.charAt(0).toUpperCase();
        if(ui.activeConversation.status) ui.activeConversation.status.className = 'absolute bottom-0 right-0 w-2.5 h-2.5 border-2 rounded-full border-gray-50 dark:border-gray-800 ';

        if (!conv.is_group && other && ui.activeConversation.infoBtn) {
            ui.activeConversation.infoBtn.onclick = () => showInfoModal(other.user.id);
            ui.activeConversation.infoBtn.classList.remove('hidden');
        } else if (ui.activeConversation.infoBtn) {
            ui.activeConversation.infoBtn.classList.add('hidden');
        }

        fetchMessages(conversationId);
        connectWebSocket(conversationId);

        if (window.innerWidth < 768) {
            if(ui.sidebar.container) ui.sidebar.container.classList.add('hidden');
            if(ui.main) ui.main.classList.remove('hidden');
        }
    }

    function showConversationsSidebar() {
        if (window.innerWidth < 768) {
            if(ui.sidebar.container) ui.sidebar.container.classList.remove('hidden');
            if(ui.main) ui.main.classList.add('hidden');
            state.activeConversationId = null;
            if (state.socket) state.socket.close();
        }
    }

    // --- MESSAGES ---
    async function fetchMessages(conversationId) {
        if(ui.message.list) ui.message.list.innerHTML = '';
        state.lastMessageDate = null;
        try {
            const data = await apiFetch(`/api/chat/conversations/${conversationId}/messages/`);
            data.results.forEach(m => appendMessage(m, false));
            setTimeout(scrollToBottom, 100);
        } catch (e) {
            showToast(e.message, 'error');
        }
    }

function appendMessage(message, animate = true) {
    if (!message || !message.sender) {
        console.error('Mensagem inválida recebida, faltando objeto sender:', message);
        return;
    }

    const messageDate = new Date(message.created_at);
    
    // CORREÇÃO: Resetar state.lastMessageDate se for null ou verificar mudança de data
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
        console.error(`Template de mensagem não encontrado: #${templateId}`);
        return;
    }

    const item = template.content.cloneNode(true);
    const messageElement = item.firstElementChild;

    // --- Selecionar elementos do template ---
    const senderNameEl = messageElement.querySelector('.sender-name');
    const messageTextEl = messageElement.querySelector('.message-text');
    const userAvatarEl = messageElement.querySelector('.user-avatar');
    const timestampEl = messageElement.querySelector('.timestamp');
    const readStatusEl = messageElement.querySelector('.read-status');

    // --- Preencher dados ---
    if (messageTextEl) messageTextEl.innerHTML = message.text;
    if (timestampEl) timestampEl.textContent = formatTime(message.created_at);

    // --- Lógica de Avatar ---
    const setupAvatar = (element, imageUrl, initial) => {
        if (!element) return;
        if (imageUrl) {
            element.innerHTML = `<img src="${imageUrl}" class="w-full h-full rounded-full object-cover">`;
        } else {
            element.innerHTML = `<span>${initial}</span>`;
            // Adiciona um gradiente genérico se não houver imagem
            element.classList.add('bg-gradient-to-br', 'from-gray-500', 'to-gray-600');
        }
    };

    if (isOwn) {
        const initial = (state.currentUser.username || 'V').charAt(0).toUpperCase();
        setupAvatar(userAvatarEl, state.currentUser.imageUrl, initial);
        
        // --- Lógica de Status ---
        if (readStatusEl) {
            let statusIcon = '';
            switch (message.status) {
                case 'sent':
                    statusIcon = '<i class="fas fa-check text-gray-400"></i>'; // Cinza
                    break;
                case 'delivered':
                    statusIcon = '<i class="fas fa-check-double text-gray-400"></i>'; // Cinza
                    break;
                case 'read':
                    statusIcon = '<i class="fas fa-check-double text-blue-400"></i>'; // Azul
                    break;
                default:
                    statusIcon = '<i class="far fa-clock text-gray-400"></i>'; // Enviando
            }
            readStatusEl.innerHTML = statusIcon;
        }
    } else {
        const senderDisplayName = message.sender.display_name || 'Usuário';
        const initial = senderDisplayName.charAt(0).toUpperCase();
        if (senderNameEl) senderNameEl.textContent = senderDisplayName;
        setupAvatar(userAvatarEl, message.sender.image_url, initial);
    }

    // --- Adicionar ao DOM ---
    if (ui.message.list) {
        if (animate) {
            messageElement.classList.add('opacity-0');
            setTimeout(() => messageElement.classList.remove('opacity-0'), 10);
        }
        ui.message.list.appendChild(messageElement);
        if (animate) {
            scrollToBottom();
        }
    } else {
        console.error("Elemento da lista de mensagens não encontrado!");
    }
}

    async function handleSendMessage(e) {
        e.preventDefault();
        if (!ui.message.input) return;
        const text = ui.message.input.value.trim();
        if (!text && !state.selectedFile) return;

        ui.message.input.focus();

        if (state.selectedFile) {
            const formData = new FormData();
            if(text) formData.append('text', text);
            formData.append('attachment', state.selectedFile);
            try {
                await apiFetch(`/api/chat/conversations/${state.activeConversationId}/messages/`, {
                    method: 'POST',
                    body: formData,
                });
                removeSelectedFile();
            } catch (e) {
                showToast(e.message, 'error');
            }
        } else if (state.socket && state.socket.readyState === WebSocket.OPEN) {
            state.socket.send(JSON.stringify({ type: 'message.send', text }));
        }
        ui.message.input.value = '';
    }

    // --- FILE HANDLING ---
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) { // 5MB
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
    function connectWebSocket(conversationId) {
        if (state.socket) state.socket.close();
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        state.socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${conversationId}/`);

        state.socket.onopen = () => console.log('WebSocket connected.');
        state.socket.onclose = () => console.log('WebSocket disconnected.');
        state.socket.onerror = (err) => console.error('WebSocket error:', err);
        state.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            switch (data.type) {
                case 'message.receive':
                    if (data.message.conversation.id === state.activeConversationId) {
                        appendMessage(data.message);
                    }
                    fetchAndRenderConversations(); // Refresh list
                    break;
                case 'typing.indicator':
                    if (data.user_id !== state.currentUser.id) {
                        const indicator = ui.typingIndicator.container;
                        const userSpan = ui.typingIndicator.user;
                        if (indicator && userSpan) {
                            if (data.action === 'start') {
                                userSpan.textContent = data.user_name;
                                indicator.classList.remove('hidden');
                            } else {
                                indicator.classList.add('hidden');
                            }
                        }
                    }
                    break;
                case 'presence.update':
                    if (data.user_id !== state.currentUser.id) {
                        const presenceText = ui.activeConversation.presence;
                        const statusDot = ui.activeConversation.status;
                        if (presenceText && statusDot) {
                            if (data.status === 'online') {
                                presenceText.textContent = 'Online';
                                statusDot.classList.remove('bg-gray-400');
                                statusDot.classList.add('bg-green-500');
                            } else {
                                presenceText.textContent = 'Offline';
                                statusDot.classList.remove('bg-green-500');
                                statusDot.classList.add('bg-gray-400');
                            }
                        }
                    }
                    break;
            }
        };
    }

    // --- EVENT LISTENERS ---
    function setupEventListeners() {
        if(ui.sidebar.newConversationBtn) ui.sidebar.newConversationBtn.addEventListener('click', startNewConversation);
        if(ui.sidebar.tabs) ui.sidebar.tabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
        if(ui.activeConversation.backBtn) ui.activeConversation.backBtn.addEventListener('click', showConversationsSidebar);
        if(ui.message.form) ui.message.form.addEventListener('submit', handleSendMessage);
        if(ui.message.attachFileBtn) ui.message.attachFileBtn.addEventListener('click', () => ui.message.fileInput.click());
        if(ui.message.fileInput) ui.message.fileInput.addEventListener('change', handleFileSelect);
        if(ui.filePreview.removeBtn) ui.filePreview.removeBtn.addEventListener('click', removeSelectedFile);
        if(ui.infoModal.closeBtn) ui.infoModal.closeBtn.addEventListener('click', hideInfoModal);
        if(ui.infoModal.container) ui.infoModal.container.addEventListener('click', (e) => {
            if (e.target === ui.infoModal.container) {
                hideInfoModal();
            }
        });

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
                    }, 2000); // 2 segundos de inatividade
                }
            });
        }
    }

    // --- INITIALIZATION ---
    function init() {
        setupEventListeners();
        switchTab('conversations'); // Load initial tab
        if (window.innerWidth >= 768) {
            if(ui.main) ui.main.classList.remove('hidden');
        } else {
            if(ui.main) ui.main.classList.add('hidden');
        }
    }

    init();
});