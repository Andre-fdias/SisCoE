document.addEventListener('DOMContentLoaded', function() {
    // Elementos da UI
    const chatContainer = document.getElementById('chat-container');
    const conversationListEl = document.getElementById('conversation-list');
    const messageListEl = document.getElementById('message-list');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const conversationNameEl = document.getElementById('conversation-name');
    const noConversationEl = document.getElementById('no-conversation-selected');
    const activeConversationEl = document.getElementById('active-conversation');
    const conversationsSidebar = document.getElementById('conversations-sidebar');
    const typingIndicator = document.getElementById('typing-indicator');
    const connectionStatus = document.getElementById('connection-status');

    // Elementos de controle
    const newConversationBtn = document.getElementById('new-conversation-btn');
    const createConversationBtn = document.getElementById('create-conversation-btn');
    const newConversationModal = document.getElementById('new-conversation-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelModalBtn = document.getElementById('cancel-modal');
    const backToConversationsBtn = document.getElementById('back-to-conversations');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle');
    const attachBtn = document.getElementById('attach-btn');
    const attachmentArea = document.getElementById('attachment-area');
    const closeAttachBtn = document.getElementById('close-attach');

    // Dados do usuário
    const currentUserId = chatContainer.dataset.userId;
    const currentUsername = chatContainer.dataset.username;
    const csrfToken = chatContainer.dataset.csrfToken;

    // Estado da aplicação
    let currentSocket = null;
    let activeConversationId = null;
    let conversations = [];
    let typingTimeout = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    // --- FUNÇÕES PRINCIPAIS ---

    /**
     * Inicializa a aplicação
     */
    function init() {
        setupEventListeners();
        fetchConversations();
        setupServiceWorker();
        updateUserPresence('online');
    }

    /**
     * Configura todos os event listeners
     */
    function setupEventListeners() {
        // Navegação
        newConversationBtn.addEventListener('click', showNewConversationModal);
        closeModalBtn.addEventListener('click', hideNewConversationModal);
        cancelModalBtn.addEventListener('click', hideNewConversationModal);
        createConversationBtn.addEventListener('click', createConversation);
        backToConversationsBtn.addEventListener('click', showConversationsSidebar);
        sidebarToggleBtn.addEventListener('click', hideConversationsSidebar);

        // Mensagens
        messageForm.addEventListener('submit', sendMessage);
        messageInput.addEventListener('input', handleTyping);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(e);
            }
        });

        // Anexos
        attachBtn.addEventListener('click', toggleAttachmentArea);
        closeAttachBtn.addEventListener('click', toggleAttachmentArea);

        // Modal - seleção de usuários
        document.querySelectorAll('.user-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = item.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                    updateCreateButtonState();
                }
            });
        });

        // Fechar modal ao clicar fora
        newConversationModal.addEventListener('click', (e) => {
            if (e.target === newConversationModal) {
                hideNewConversationModal();
            }
        });

        // Reconexão quando online
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Visibilidade da página para atualizar presença
        document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    /**
     * Busca e exibe as conversas do usuário
     */
async function fetchConversations() {
    showLoading();
    try {
        const response = await fetch('/api/chat/conversations/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include'  // ← ADICIONE ESTA LINHA
        });
        
        if (!response.ok) throw new Error('Falha ao buscar conversas');
        
        conversations = await response.json();
        renderConversations();
        
    } catch (error) {
        console.error('Erro ao buscar conversas:', error);
        showError('Erro ao carregar conversas');
    } finally {
        hideLoading();
    }
}

    /**
     * Renderiza a lista de conversas
     */
    function renderConversations() {
        if (conversations.length === 0) {
            conversationListEl.innerHTML = `
                <div class="p-8 text-center text-gray-500">
                    <i class="fas fa-comments text-4xl mb-4 text-gray-300"></i>
                    <p>Nenhuma conversa encontrada</p>
                    <button class="mt-4 px-4 py-2 bg-[var(--whatsapp-green)] text-white rounded-lg hover:bg-[var(--whatsapp-green-dark)] transition-colors">
                        Iniciar uma conversa
                    </button>
                </div>
            `;
            return;
        }

        conversationListEl.innerHTML = conversations.map(conv => {
            const displayName = getConversationDisplayName(conv);
            const lastMessage = conv.last_message;
            const unreadCount = conv.unread_count || 0;
            const isActive = conv.id === activeConversationId;
            
            return `
                <div class="conversation-item p-3 cursor-pointer hover:bg-gray-50 transition-colors ${isActive ? 'active' : ''} ${unreadCount > 0 ? 'unread' : ''}"
                     data-conversation-id="${conv.id}">
                    <div class="flex items-center space-x-3">
                        <div class="relative">
                            <img class="w-12 h-12 rounded-full object-cover" 
                                 src="${getConversationAvatar(conv)}" 
                                 alt="${displayName}">
                            ${unreadCount > 0 ? `
                                <span class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                    ${unreadCount}
                                </span>
                            ` : ''}
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between items-start">
                                <h4 class="font-semibold text-gray-900 truncate">${displayName}</h4>
                                ${lastMessage ? `
                                    <span class="text-xs text-gray-500 whitespace-nowrap">
                                        ${formatTime(lastMessage.created_at)}
                                    </span>
                                ` : ''}
                            </div>
                            <div class="flex justify-between items-center">
                                <p class="text-sm text-gray-600 truncate">
                                    ${lastMessage ? formatMessagePreview(lastMessage) : 'Nenhuma mensagem'}
                                </p>
                                ${unreadCount > 0 ? `
                                    <span class="bg-[var(--whatsapp-green)] rounded-full w-2 h-2 flex-shrink-0 ml-2"></span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Adiciona event listeners às conversas
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const conversationId = item.dataset.conversationId;
                const conversation = conversations.find(c => c.id === conversationId);
                if (conversation) {
                    selectConversation(conversation);
                }
            });
        });
    }

    /**
     * Seleciona uma conversa
     */
    function selectConversation(conversation) {
        activeConversationId = conversation.id;
        
        // Atualiza UI
        hideConversationsSidebar();
        noConversationEl.classList.add('hidden');
        activeConversationEl.classList.remove('hidden');
        
        // Atualiza header
        conversationNameEl.textContent = getConversationDisplayName(conversation);
        document.getElementById('conversation-avatar').src = getConversationAvatar(conversation);
        
        // Conecta WebSocket e carrega mensagens
        connectWebSocket(conversation.id);
        fetchMessages(conversation.id);
        
        // Atualiza presença
        updateConversationPresence(conversation);
        
        // Marca como lida
        markConversationAsRead(conversation.id);
        
        // Atualiza lista de conversas
        renderConversations();
    }

    /**
     * Conecta ao WebSocket da conversa
     */
    function connectWebSocket(conversationId) {
        // Fecha conexão anterior
        if (currentSocket) {
            currentSocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}/`;
        
        currentSocket = new WebSocket(wsUrl);
        
        currentSocket.onopen = () => {
            console.log('WebSocket conectado');
            reconnectAttempts = 0;
            updateConnectionStatus('connected');
        };
        
        currentSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            handleWebSocketMessage(data);
        };
        
        currentSocket.onclose = (e) => {
            console.log('WebSocket desconectado:', e);
            handleWebSocketClose();
        };
        
        currentSocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };
    }

    /**
     * Processa mensagens do WebSocket
     */
    function handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message.receive':
                appendMessage(data.message);
                playMessageSound();
                break;
                
            case 'message.update':
                updateMessage(data.message);
                break;
                
            case 'message.delete':
                deleteMessage(data.message_id);
                break;
                
            case 'message.reaction':
                updateMessageReaction(data.message_id, data.reaction);
                break;
                
            case 'typing.indicator':
                showTypingIndicator(data.user_id, data.user_name, data.action);
                break;
                
            case 'presence.update':
                updateUserPresenceIndicator(data.user_id, data.status);
                break;
                
            case 'message.status':
                updateMessageStatus(data.message_id, data.status, data.user_id);
                break;
                
            case 'error':
                showError(data.message);
                break;
        }
    }

    /**
     * Lida com fechamento do WebSocket
     */
    function handleWebSocketClose() {
        updateConnectionStatus('disconnected');
        
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`Tentando reconectar em ${delay}ms...`);
            
            setTimeout(() => {
                if (activeConversationId) {
                    connectWebSocket(activeConversationId);
                }
                reconnectAttempts++;
            }, delay);
        }
    }

    /**
     * Busca mensagens da conversa
     */
async function fetchMessages(conversationId) {
    showLoading();
    try {
        const response = await fetch(`/api/chat/conversations/${conversationId}/messages/`, {
            credentials: 'include'  // ← ADICIONE ESTA LINHA
        });
        if (!response.ok) throw new Error('Falha ao buscar mensagens');
        
        const messages = await response.json();
        renderMessages(messages);
        
    } catch (error) {
        console.error('Erro ao buscar mensagens:', error);
        showError('Erro ao carregar mensagens');
    } finally {
        hideLoading();
    }
}

    /**
     * Renderiza mensagens na tela
     */
    function renderMessages(messages) {
        messageListEl.innerHTML = '';
        
        if (messages.length === 0) {
            messageListEl.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-comment-slash text-4xl mb-4 text-gray-300"></i>
                    <p>Nenhuma mensagem ainda</p>
                    <p class="text-sm">Envie uma mensagem para iniciar a conversa</p>
                </div>
            `;
            return;
        }

        messages.forEach(message => {
            appendMessage(message, false);
        });
        
        scrollToBottom();
    }

    /**
     * Adiciona uma mensagem à lista
     */
    function appendMessage(message, animate = true) {
        const messageElement = createMessageElement(message);
        
        if (animate) {
            messageElement.classList.add('message-enter');
        }
        
        messageListEl.appendChild(messageElement);
        scrollToBottom();
        
        // Atualiza última mensagem na lista de conversas
        updateConversationLastMessage(message.conversation, message);
    }

    /**
     * Cria elemento HTML para uma mensagem
     */
    function createMessageElement(message) {
        const isOwn = message.sender.id == currentUserId;
        const senderName = isOwn ? 'Você' : getDisplayName(message.sender);
        const timestamp = formatTime(message.created_at);
        const statusIcon = getMessageStatusIcon(message);
        
        return document.createElement('div').innerHTML = `
            <div class="flex ${isOwn ? 'justify-end' : 'justify-start'} mb-2 message-enter" data-message-id="${message.id}">
                <div class="max-w-xs lg:max-w-md ${isOwn ? 'message-sent' : 'message-received'} p-3">
                    ${!isOwn ? `
                        <div class="text-xs font-semibold text-gray-700 mb-1">${senderName}</div>
                    ` : ''}
                    
                    ${message.parent_message ? `
                        <div class="bg-gray-100 rounded p-2 mb-2 border-l-4 border-gray-400">
                            <div class="text-xs font-semibold text-gray-600">
                                ${message.parent_message.sender_name}
                            </div>
                            <div class="text-xs text-gray-600 truncate">
                                ${message.parent_message.text}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="text-sm text-gray-900">${escapeHtml(message.text)}</div>
                    
                    ${message.attachments && message.attachments.length > 0 ? `
                        <div class="mt-2 space-y-2">
                            ${message.attachments.map(att => `
                                <div class="border rounded-lg p-2 bg-white">
                                    <div class="flex items-center space-x-2">
                                        <i class="fas fa-file text-gray-500"></i>
                                        <span class="text-xs text-gray-700">${att.file_type}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="flex justify-between items-center mt-1">
                        <span class="message-timestamp">${timestamp}</span>
                        ${isOwn ? `
                            <div class="flex items-center space-x-1 ml-2">
                                ${statusIcon}
                                ${message.edited ? '<span class="text-xs text-gray-500">(editado)</span>' : ''}
                            </div>
                        ` : ''}
                    </div>
                    
                    ${message.reactions && message.reactions.length > 0 ? `
                        <div class="flex flex-wrap gap-1 mt-1">
                            ${message.reactions.map(reaction => `
                                <span class="bg-gray-200 rounded-full px-2 py-1 text-xs">
                                    ${reaction.emoji}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Envia uma mensagem
     */
    function sendMessage(e) {
        e.preventDefault();
        
        const text = messageInput.value.trim();
        if (!text || !currentSocket || currentSocket.readyState !== WebSocket.OPEN) {
            return;
        }

        // Envia via WebSocket
        currentSocket.send(JSON.stringify({
            type: 'message.send',
            message: text
        }));

        // Limpa input
        messageInput.value = '';
        
        // Para indicador de digitação
        stopTyping();
    }

    /**
     * Mostra/oculta indicador de digitação
     */
    function handleTyping() {
        if (!currentSocket || currentSocket.readyState !== WebSocket.OPEN) {
            return;
        }

        // Envia evento de início de digitação
        currentSocket.send(JSON.stringify({
            type: 'typing.start'
        }));

        // Limpa timeout anterior
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }

        // Configura timeout para parar de digitar
        typingTimeout = setTimeout(() => {
            stopTyping();
        }, 1000);
    }

    function stopTyping() {
        if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
            currentSocket.send(JSON.stringify({
                type: 'typing.stop'
            }));
        }
        
        if (typingTimeout) {
            clearTimeout(typingTimeout);
            typingTimeout = null;
        }
    }

    // --- FUNÇÕES AUXILIARES ---

    function getConversationDisplayName(conversation) {
        if (conversation.name) return conversation.name;
        
        if (!conversation.is_group && conversation.participants) {
            const otherParticipant = conversation.participants.find(p => p.user.id != currentUserId);
            if (otherParticipant) {
                return getDisplayName(otherParticipant.user);
            }
        }
        
        return 'Conversa sem nome';
    }

    function getDisplayName(user) {
        const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
        return fullName || user.email || 'Usuário';
    }

    function getConversationAvatar(conversation) {
        // Implementar lógica para avatar da conversa
        return conversation.is_group ? 
            '/static/images/default-group.png' : 
            '/static/images/default-avatar.png';
    }

    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    function formatMessagePreview(message) {
        if (!message.text) return '📎 Anexo';
        return message.text.length > 50 ? 
            message.text.substring(0, 50) + '...' : 
            message.text;
    }

    function getMessageStatusIcon(message) {
        // Implementar lógica de status (entregue, lido, etc.)
        return '<i class="fas fa-check text-gray-400 text-xs"></i>';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scrollToBottom() {
        const messageArea = document.getElementById('message-area');
        if (messageArea) {
            messageArea.scrollTop = messageArea.scrollHeight;
        }
    }

    function showLoading() {
        document.getElementById('loading-spinner').classList.remove('hidden');
    }

    function hideLoading() {
        document.getElementById('loading-spinner').classList.add('hidden');
    }

    function showError(message) {
        // Implementar notificação de erro
        console.error('Erro:', message);
    }

    function playMessageSound() {
        // Implementar som de notificação
    }

    function updateConnectionStatus(status) {
        const statusMap = {
            connected: { text: '● Online', color: 'bg-green-500' },
            disconnected: { text: '● Offline', color: 'bg-red-500' },
            error: { text: '● Erro', color: 'bg-red-500' }
        };
        
        const statusInfo = statusMap[status] || statusMap.disconnected;
        connectionStatus.textContent = statusInfo.text;
        connectionStatus.className = `${statusInfo.color} px-2 py-1 rounded-full text-xs text-white`;
    }

    // --- MODAL NOVA CONVERSA ---

    function showNewConversationModal() {
        newConversationModal.classList.remove('hidden');
        updateUserPresenceInModal();
    }

    function hideNewConversationModal() {
        newConversationModal.classList.add('hidden');
        // Limpa seleções
        document.querySelectorAll('#modal-user-list input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
        document.getElementById('group-name-input').value = '';
    }

    function updateCreateButtonState() {
        const selectedUsers = Array.from(
            document.querySelectorAll('#modal-user-list input[type="checkbox"]:checked')
        ).map(cb => cb.value);
        
        createConversationBtn.disabled = selectedUsers.length === 0;
    }

async function createConversation() {
    const selectedUsers = Array.from(
        document.querySelectorAll('#modal-user-list input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    
    const groupName = document.getElementById('group-name-input').value.trim();
    const isGroup = selectedUsers.length > 1 || groupName !== '';

    if (selectedUsers.length === 0) {
        showError('Selecione pelo menos um usuário');
        return;
    }

    showLoading();
    try {
        const response = await fetch('/api/chat/conversations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                name: groupName,
                is_group: isGroup,
                participants_ids: [...selectedUsers, currentUserId]
            }),
            credentials: 'include'  // ← ADICIONE ESTA LINHA
        });

        if (!response.ok) throw new Error('Falha ao criar conversa');
        
        const newConversation = await response.json();
        hideNewConversationModal();
        
        conversations.unshift(newConversation);
        renderConversations();
        selectConversation(newConversation);

    } catch (error) {
        console.error('Erro ao criar conversa:', error);
        showError('Erro ao criar conversa');
    } finally {
        hideLoading();
    }
}

    // --- RESPONSIVIDADE ---

    function showConversationsSidebar() {
        conversationsSidebar.classList.remove('hidden');
        activeConversationEl.classList.add('hidden');
        noConversationEl.classList.remove('hidden');
    }

    function hideConversationsSidebar() {
        if (window.innerWidth < 768) {
            conversationsSidebar.classList.add('hidden');
        }
    }

    // --- PRESENÇA E STATUS ---

async function updateUserPresence(status) {
    try {
        await fetch('/api/chat/presence/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ status }),
            credentials: 'include'  // ← ADICIONE ESTA LINHA
        });
    } catch (error) {
        console.error('Erro ao atualizar presença:', error);
    }
}

async function updateUserPresenceInModal() {
    try {
        const response = await fetch('/api/chat/presence/');
        const presenceData = await response.json();
        
        // Atualiza status dos usuários no modal
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            const userId = indicator.dataset.userId;
            const status = presenceData[userId]?.status || 'offline';
            indicator.className = `status-indicator status-${status}`;
        });
    } catch (error) {
        console.error('Erro ao buscar presença:', error);
    }
}
    function updateConversationPresence(conversation) {
        // Atualiza status dos participantes na conversa atual
        // Implementar busca de presença
    }

    function updateUserPresenceIndicator(userId, status) {
        // Atualiza indicador de presença na UI
        const indicators = document.querySelectorAll(`.status-indicator[data-user-id="${userId}"]`);
        indicators.forEach(indicator => {
            indicator.className = `status-indicator status-${status}`;
        });
    }

    function showTypingIndicator(userId, userName, action) {
        if (action === 'start') {
            typingIndicator.classList.remove('hidden');
            // Atualiza texto com nome do usuário
            const typingText = typingIndicator.querySelector('.typing-text');
            if (typingText) {
                typingText.textContent = `${userName} está digitando...`;
            }
        } else {
            typingIndicator.classList.add('hidden');
        }
    }

    // --- EVENT HANDLERS GLOBAIS ---

    function handleOnline() {
        updateConnectionStatus('connected');
        if (activeConversationId) {
            connectWebSocket(activeConversationId);
        }
    }

    function handleOffline() {
        updateConnectionStatus('disconnected');
    }

    function handleVisibilityChange() {
        if (!document.hidden) {
            updateUserPresence('online');
        }
    }

    function setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => console.log('SW registered'))
                .catch(error => console.log('SW registration failed'));
        }
    }

    // Funções placeholder para funcionalidades futuras
    function updateMessage(message) {}
    function deleteMessage(messageId) {}
    function updateMessageReaction(messageId, reaction) {}
    function updateMessageStatus(messageId, status, userId) {}
    function markConversationAsRead(conversationId) {}
    function updateConversationLastMessage(conversationId, message) {}

    // Inicializa a aplicação
    init();
});


function connectWebSocket(conversationId) {
    console.log('Tentando conectar WebSocket para conversa:', conversationId);
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}/`;
    
    console.log('URL do WebSocket:', wsUrl);
    
    currentSocket = new WebSocket(wsUrl);
    
    currentSocket.onopen = () => {
        console.log('✅ WebSocket conectado com sucesso');
        updateConnectionStatus('connected');
    };
    
    currentSocket.onerror = (error) => {
        console.error('❌ Erro WebSocket:', error);
        updateConnectionStatus('error');
    };
}


async function updateUserPresenceInModal() {
    try {
        // Primeiro, busca todos os usuários disponíveis
        const userIds = Array.from(document.querySelectorAll('.user-item input[type="checkbox"]'))
            .map(input => input.value);
        
        if (userIds.length === 0) return;
        
        const response = await fetch(`/api/chat/presence/?user_ids=${userIds.join(',')}`, {
            credentials: 'include'
        });
        
        if (!response.ok) return;
        
        const presenceData = await response.json();
        
        // Atualiza status dos usuários no modal
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            const userId = indicator.dataset.userId;
            const status = presenceData[userId]?.status || 'offline';
            indicator.className = `status-indicator status-${status}`;
        });
    } catch (error) {
        console.error('Erro ao buscar presença:', error);
    }
}