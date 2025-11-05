
document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENTOS DA UI ---

    const ui = {

        chatContainer: document.getElementById('chat-container'),

        conversations: {

            sidebar: document.getElementById('conversations-sidebar'),

            list: document.getElementById('conversation-list'),

            loading: document.getElementById('conversation-loading'),

            empty: document.getElementById('conversation-empty'),

            container: document.getElementById('conversations-container'),

            refreshBtn: document.getElementById('refresh-conversations'),

        },

        activeConversation: {

            container: document.getElementById('active-conversation'),

            name: document.getElementById('conversation-name'),

            avatar: document.getElementById('conversation-avatar'),

            presence: document.getElementById('conversation-presence'),

            status: document.getElementById('conversation-status'),

            backBtn: document.getElementById('back-to-conversations'),

        },

        messages: {

            area: document.getElementById('message-area'),

            list: document.getElementById('message-list'),

            form: document.getElementById('message-form'),

            input: document.getElementById('message-input'),

            sendBtn: document.getElementById('send-btn'),

        },

        modal: {

            container: document.getElementById('new-conversation-modal'),

            openBtns: document.querySelectorAll('#new-conversation-btn, #empty-new-conversation-btn, #quick-new-conversation'),

            closeBtns: document.querySelectorAll('#close-modal, #cancel-modal'),

            createBtn: document.getElementById('create-conversation-btn'),

            groupNameInput: document.getElementById('group-name-input'),

            userList: document.getElementById('modal-user-list'),

            selectedCount: document.getElementById('selected-count'),

        },

        initialScreen: document.getElementById('no-conversation-selected'),

        connectionStatus: document.getElementById('connection-status'),

        typingIndicator: {

            container: document.getElementById('typing-indicator'),

            user: document.getElementById('typing-user'),

        },

        loadingSpinner: document.getElementById('loading-spinner'),

        toastContainer: document.getElementById('toast-container'),

    };



    // --- DADOS E ESTADO DA APLICAÇÃO ---

    const state = {

        currentUser: {

            id: ui.chatContainer.dataset.userId,

            username: ui.chatContainer.dataset.username,

            csrfToken: ui.chatContainer.dataset.csrfToken,

        },

        socket: null,

        activeConversationId: null,

        conversations: new Map(),

        typingTimeout: null,

        reconnect: {

            attempts: 0,

            maxAttempts: 5,

            delay: 1000,

        },

    };



    // --- FUNÇÕES DE API ---



    async function apiFetch(url, options = {}) {

        const defaultHeaders = {

            'X-Requested-With': 'XMLHttpRequest',

            'Content-Type': 'application/json',

            'X-CSRFToken': state.currentUser.csrfToken,

        };

        const response = await fetch(url, {

            ...options,

            headers: { ...defaultHeaders, ...options.headers },

        });



        if (!response.ok) {

            const errorText = await response.text();

            console.error("Server error response:", errorText);

            try {

                const errorData = JSON.parse(errorText);

                throw new Error(errorData.detail || 'Falha na requisição API.');

            } catch (e) {

                throw new Error(errorText || 'Falha na requisição API.');

            }

        }



        return response.status === 204 ? null : response.json();

    }



    // --- FUNÇÕES DE UI ---



    function showToast(message, isError = false) {

        const toast = document.createElement('div');

        toast.className = `p-4 rounded-lg shadow-xl text-white fade-in max-w-sm ${isError ? 'bg-red-500' : 'bg-green-500'}`;

        toast.textContent = message;

        ui.toastContainer.appendChild(toast);

        setTimeout(() => toast.remove(), 5000);

    }



    function toggleLoading(show) {

        ui.loadingSpinner.classList.toggle('hidden', !show);

    }



    function formatTime(timestamp) {

        if (!timestamp) return '';

        return new Date(timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    }



    function scrollToBottom() {

        ui.messages.area.scrollTop = ui.messages.area.scrollHeight;

    }



    // --- LÓGICA DE CONVERSAS ---



    async function fetchConversations() {

        toggleLoading(true);

        ui.conversations.loading.classList.remove('hidden');

        ui.conversations.list.innerHTML = '';

        try {

            const convs = await apiFetch('/api/chat/conversations/');

            state.conversations.clear();

            convs.forEach(conv => state.conversations.set(conv.id, conv));

            renderConversationList();

        } catch (error) {

            showToast(error.message, true);

            ui.conversations.empty.classList.remove('hidden');

        } finally {

            toggleLoading(false);

            ui.conversations.loading.classList.add('hidden');

        }

    }



    function renderConversationList() {

        ui.conversations.list.innerHTML = '';

        if (state.conversations.size === 0) {

            ui.conversations.empty.classList.remove('hidden');

            return;

        }

        ui.conversations.empty.classList.add('hidden');



        const sortedConversations = [...state.conversations.values()].sort((a, b) => 

            new Date(b.updated_at) - new Date(a.updated_at)

        );



        sortedConversations.forEach(conv => {

            const otherParticipant = conv.participants.find(p => p.user.id != state.currentUser.id);

            const displayName = conv.is_group ? conv.name : (otherParticipant?.user.display_name || 'Conversa');

            const lastMessage = conv.last_message;

            const unreadCount = conv.unread_count || 0;



            const item = document.createElement('div');

            item.className = `conversation-item p-3 cursor-pointer flex items-center space-x-3 ${conv.id === state.activeConversationId ? 'active' : ''} ${unreadCount > 0 ? 'unread' : ''}`;

            item.dataset.conversationId = conv.id;

            item.innerHTML = `

                <div class="relative flex-shrink-0">

                    <div class="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center">

                        <i class="fas ${conv.is_group ? 'fa-users' : 'fa-user'} text-white"></i>

                    </div>

                </div>

                <div class="flex-1 min-w-0">

                    <div class="flex justify-between items-start">

                        <h4 class="font-semibold text-gray-900 truncate">${displayName}</h4>

                        <span class="text-xs text-gray-500 whitespace-nowrap">${lastMessage ? formatTime(lastMessage.created_at) : ''}</span>

                    </div>

                    <div class="flex justify-between items-center">

                        <p class="text-sm text-gray-600 truncate flex-1 pr-2">${lastMessage ? lastMessage.text : 'Nenhuma mensagem'}</p>

                        ${unreadCount > 0 ? `<span class="bg-green-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">${unreadCount}</span>` : ''}

                    </div>

                </div>

            `;

            item.addEventListener('click', () => selectConversation(conv.id));

            ui.conversations.list.appendChild(item);

        });

    }



    function selectConversation(conversationId) {

        console.log('Selecionando conversa com ID:', conversationId);

        if (state.activeConversationId === conversationId) return;

        state.activeConversationId = conversationId;

        const conversation = state.conversations.get(conversationId);



        if (!conversation) {

            state.activeConversationId = null;

            return;

        }



        ui.initialScreen.classList.add('hidden');

        ui.activeConversation.container.classList.remove('hidden');



        const otherParticipant = conversation.participants.find(p => p.user.id != state.currentUser.id);

        ui.activeConversation.name.textContent = conversation.is_group ? conversation.name : (otherParticipant?.user.display_name || 'Conversa');

        

        renderConversationList(); // Para destacar a conversa ativa

        fetchMessages(conversationId);

        connectWebSocket(conversationId);



        if (window.innerWidth < 768) { // Em mobile, esconde a lista

            ui.conversations.sidebar.classList.add('hidden');

        }

    }

    

    function showConversationsSidebar() {

        if (window.innerWidth < 768) {

            ui.conversations.sidebar.classList.remove('hidden');

            ui.activeConversation.container.classList.add('hidden');

            state.activeConversationId = null;

            if (state.socket) state.socket.close();

            renderConversationList();

        }

    }



    // --- LÓGICA DE MENSAGENS ---



    async function fetchMessages(conversationId) {

        toggleLoading(true);

        ui.messages.list.innerHTML = '<p class="text-center text-gray-500">Carregando mensagens...</p>';

        try {

            const paginatedResponse = await apiFetch(`/api/chat/conversations/${conversationId}/messages/`);

            renderMessages(paginatedResponse);

        } catch (error) {

            showToast(error.message, true);

            ui.messages.list.innerHTML = '<p class="text-center text-red-500">Erro ao carregar mensagens.</p>';

        }

        finally {

            toggleLoading(false);

        }

    }



    function renderMessages(paginatedResponse) {

        ui.messages.list.innerHTML = '';

        const messages = paginatedResponse.results; // Extrai o array de mensagens



        if (!messages || messages.length === 0) {

            ui.messages.list.innerHTML = '<div class="text-center text-gray-500 py-8"><i class="fas fa-comment-dots text-3xl mb-2"></i><p>Nenhuma mensagem ainda</p></div>';

            return;

        }

        messages.forEach(msg => appendMessage(msg, false));

        scrollToBottom();

    }



    function appendMessage(message, animate = true) {

        const isOwn = message.sender.id == state.currentUser.id;

        const messageEl = document.createElement('div');

        messageEl.className = `flex ${isOwn ? 'justify-end' : 'justify-start'} mb-2 ${animate ? 'message-enter' : ''}`;

        messageEl.dataset.messageId = message.id;

        messageEl.innerHTML = `

            <div class="max-w-xs lg:max-w-md p-3 rounded-lg ${isOwn ? 'message-sent' : 'message-received'}">

                ${!isOwn && message.conversation?.is_group ? `<div class="text-xs font-semibold text-blue-700 mb-1">${message.sender.display_name}</div>` : ''}

                <div class="text-sm text-gray-900">${message.text || ''}</div>

                <div class="text-right text-xs text-gray-500 mt-1">${formatTime(message.created_at)}</div>

            </div>

        `;

        ui.messages.list.appendChild(messageEl);

        scrollToBottom();

    }

    

    function handleSendMessage(e) {

        e.preventDefault();

        const text = ui.messages.input.value.trim();

        if (!text || !state.socket || state.socket.readyState !== WebSocket.OPEN) return;



        state.socket.send(JSON.stringify({ type: 'message.send', text: text }));

        ui.messages.input.value = '';

        handleTypingStop();

    }



    // --- LÓGICA DE WEBSOCKET ---



    function connectWebSocket(conversationId) {

        if (state.socket) state.socket.close();



        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}/`;

        

        state.socket = new WebSocket(wsUrl);



        state.socket.onopen = () => {

            console.log('WebSocket connected.');

            updateConnectionStatus('connected');

            state.reconnect.attempts = 0;

        };



        state.socket.onmessage = (e) => {

            const data = JSON.parse(e.data);

            handleWebSocketMessage(data);

        };



        state.socket.onclose = () => {

            console.log('WebSocket disconnected.');

            updateConnectionStatus('disconnected');

            handleWebSocketClose();

        };



        state.socket.onerror = (err) => {

            console.error('WebSocket error:', err);

            updateConnectionStatus('error');

        };

    }



    function handleWebSocketMessage(data) {

        switch (data.type) {

            case 'message.receive':

                appendMessage(data.message);

                // Atualiza a lista de conversas para mostrar a última mensagem

                fetchConversations();

                break;

            case 'typing.indicator':

                if (data.user_id !== state.currentUser.id) {

                    showTypingIndicator(data.user_name, data.action === 'start');

                }

                break;

            case 'presence.update':

                // Lógica para atualizar status de presença na UI

                break;

            case 'error':

                showToast(`Erro do servidor: ${data.message}`, true);

                break;

        }

    }



    function handleWebSocketClose() {

        if (state.reconnect.attempts < state.reconnect.maxAttempts) {

            state.reconnect.attempts++;

            const delay = state.reconnect.delay * state.reconnect.attempts;

            console.log(`Tentando reconectar em ${delay}ms...`);

            setTimeout(() => {

                if (state.activeConversationId) {

                    connectWebSocket(state.activeConversationId);

                }

            }, delay);

        } else {

            console.error('Máximo de tentativas de reconexão atingido.');

            showToast('Não foi possível conectar ao chat. Verifique sua conexão e atualize a página.', true);

        }

    }

    

    function updateConnectionStatus(status) {

        const statuses = {

            connected: { text: '● Online', color: 'bg-green-500' },

            disconnected: { text: '● Offline', color: 'bg-gray-400' },

            error: { text: '● Erro', color: 'bg-red-500' },

        };

        const current = statuses[status] || statuses.disconnected;

        ui.connectionStatus.textContent = current.text;

        ui.connectionStatus.className = `px-2 py-1 rounded-full text-xs text-white ${current.color}`;

    }



    // --- INDICADOR "DIGITANDO" ---



    function handleTyping() {

        if (!state.socket || state.socket.readyState !== WebSocket.OPEN) return;

        

        if (!state.typingTimeout) {

            state.socket.send(JSON.stringify({ type: 'typing.start' }));

        } else {

            clearTimeout(state.typingTimeout);

        }



        state.typingTimeout = setTimeout(handleTypingStop, 3000);

    }



    function handleTypingStop() {

        if (state.typingTimeout) {

            clearTimeout(state.typingTimeout);

            state.typingTimeout = null;

            if (state.socket && state.socket.readyState === WebSocket.OPEN) {

                state.socket.send(JSON.stringify({ type: 'typing.stop' }));

            }

        }

    }



    function showTypingIndicator(userName, isTyping) {

        if (isTyping) {

            ui.typingIndicator.user.textContent = `${userName} está digitando...`;

            ui.typingIndicator.container.classList.remove('hidden');

        } else {

            ui.typingIndicator.container.classList.add('hidden');

        }

    }



    // --- MODAL NOVA CONVERSA ---



    function showNewConversationModal() {

        ui.modal.container.classList.remove('hidden');

        // Limpa seleções anteriores

        ui.modal.userList.querySelectorAll('input:checked').forEach(cb => cb.checked = false);

        ui.modal.groupNameInput.value = '';

        updateCreateButtonState();

    }



    function hideNewConversationModal() {

        ui.modal.container.classList.add('hidden');

    }



    function updateCreateButtonState() {

        const selectedCount = ui.modal.userList.querySelectorAll('input:checked').length;

        ui.modal.selectedCount.textContent = selectedCount;

        ui.modal.createBtn.disabled = selectedCount === 0;

    }



    async function createConversation() {

        console.log("Botão de criar conversa clicado");

        const selectedUserIds = [...ui.modal.userList.querySelectorAll('input:checked')].map(cb => parseInt(cb.value, 10));

        const groupName = ui.modal.groupNameInput.value.trim();

        const isGroup = Boolean(selectedUserIds.length > 1 || (selectedUserIds.length > 0 && groupName));



        toggleLoading(true);

        try {

            const newConversation = await apiFetch('/api/chat/conversations/', {

                method: 'POST',

                body: JSON.stringify({

                    name: groupName,

                    is_group: isGroup,

                    participants_ids: selectedUserIds,

                }),

            });

            hideNewConversationModal();



            // Adiciona a nova conversa diretamente ao estado

            state.conversations.set(newConversation.id, newConversation);

            // Renderiza a lista para incluir a nova conversa

            renderConversationList();

            // Seleciona a nova conversa

            selectConversation(newConversation.id);



        } catch (error) {

            showToast(error.message, true);

        }

        finally {

            toggleLoading(false);

        }

    }



    // --- INICIALIZAÇÃO ---



    function setupEventListeners() {

        ui.conversations.refreshBtn.addEventListener('click', fetchConversations);

        ui.messages.form.addEventListener('submit', handleSendMessage);

        ui.messages.input.addEventListener('input', handleTyping);

        ui.activeConversation.backBtn.addEventListener('click', showConversationsSidebar);



        // Modal

        ui.modal.openBtns.forEach(btn => btn.addEventListener('click', showNewConversationModal));

        ui.modal.closeBtns.forEach(btn => btn.addEventListener('click', hideNewConversationModal));

        ui.modal.createBtn.addEventListener('click', createConversation);

        ui.modal.userList.addEventListener('change', updateCreateButtonState);

    }



    function init() {

        setupEventListeners();

        fetchConversations();

        // Responsividade inicial

        if (window.innerWidth >= 768) {

            ui.conversations.sidebar.classList.remove('hidden');

        } else {

            ui.activeConversation.container.classList.add('hidden');

        }

    }



    init();

});
