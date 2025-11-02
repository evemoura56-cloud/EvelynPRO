// ==== CONSTANTES E SELETORES ====
const CHAT_HISTORY_KEY = 'evelynpro_chat_history';
const STATE_KEY = 'evelynpro_app_state';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const elements = {
    chatBox: $('#messages'),
    chatForm: $('#chatForm'),
    chatInput: $('#chatInput'),
    uploadCVBtn: $('#uploadCV'),
    cvInput: $('#cvInput'),
    uploadStudyBtn: $('#uploadStudy'),
    studyInput: $('#studyInput'),
    newChatBtn: $('#newChat'),
    welcomeModal: $('#welcomeBackModal'),
    continueChatBtn: $('#continueChat'),
    startNewChatBtn: $('#startNewChat'),
    topicSelector: $('#topicSelection'),
    customTopicInput: $('#customTopicInput'),
    // Seletores de Vagas
    btnBuscarVagas: $('#btnBuscarVagas'),
    btnBuscarMatch: $('#btnBuscarMatch'),
    prefCargo: $('#prefCargo'),
    prefCidade: $('#prefCidade'),
    prefEstado: $('#prefEstado'),
    prefModelo: $('#prefModelo'),
    prefTipo: $('#prefTipo'),
    // Seletores de Animação
    avatarContainer: $('#avatarContainer'),
    thinkingIndicator: $('#thinkingIndicator'),
    
    // NOVOS SELETORES (Menu Mobile)
    openSidebar: $('#openSidebar'),
    closeSidebar: $('#closeSidebar'),
    sidebarContainer: $('#sidebarContainer'),
    sidebarOverlay: $('#sidebarOverlay'),
};

// Estado da aplicação
let appState = {
    isStudying: false,
    studySubject: null,
    studyPdf: null,
};

// ==== FUNÇÕES DE FEEDBACK VISUAL ====
function startThinking() {
    elements.avatarContainer.classList.add('thinking');
    elements.thinkingIndicator.style.display = 'block';
}

function stopThinking() {
    elements.avatarContainer.classList.remove('thinking');
    elements.thinkingIndicator.style.display = 'none';
}

// ==== FUNÇÕES PRINCIPAIS DO CHAT ====
function simpleMarkdownToHtml(text) {
    if (typeof text !== 'string') {
        text = String(text);
    }
    return text
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*/g, '')
        .replace(/(\r\n|\r|\n)/g, '<br>');
}

function addMessage(sender, message, isHtml = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    if (isHtml) {
        messageDiv.innerHTML = message;
    } else {
        messageDiv.innerHTML = simpleMarkdownToHtml(message);
    }
    elements.chatBox.appendChild(messageDiv);
    scrollToBottom();
    if (!message.includes('loading-spinner')) {
        saveChatHistory();
    }
}

function scrollToBottom() {
    elements.chatBox.scrollTop = elements.chatBox.scrollHeight;
}

function showBotLoading() {
    startThinking();
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'bot');
    loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
    elements.chatBox.appendChild(loadingDiv);
    scrollToBottom();
    return loadingDiv;
}

function saveChatHistory() {
    localStorage.setItem(CHAT_HISTORY_KEY, elements.chatBox.innerHTML);
}

function loadChatHistory() {
    const history = localStorage.getItem(CHAT_HISTORY_KEY);
    if (history) {
        elements.chatBox.innerHTML = history;
        scrollToBottom();
    }
}

function saveState() {
    localStorage.setItem(STATE_KEY, JSON.stringify(appState));
}

function loadState() {
    const state = localStorage.getItem(STATE_KEY);
    if (state) {
        appState = JSON.parse(state);
    }
}

function clearChat() {
    elements.chatBox.innerHTML = '';
    localStorage.removeItem(CHAT_HISTORY_KEY);
    localStorage.removeItem(STATE_KEY);
    appState = { isStudying: false, studySubject: null, studyPdf: null };
    showWelcomeMessage();
    // No mobile, feche o menu ao limpar o chat
    if (elements.sidebarContainer.classList.contains('mobile-open')) {
        toggleSidebar();
    }
}

/**
 * Mostra a saudação inicial (CORRIGIDO)
 */
function showWelcomeMessage() {
    // MUDANÇA: Voltamos a usar HTML e passamos 'true' para o addMessage
    addMessage('bot', `
        Olá! Eu sou a <strong>Evelyn PRO</strong>, sua agente de carreira e estudos.<br><br>
        O que posso fazer por você?
        <ul>
            <li>Analisar seu currículo (📄 Enviar Currículo)</li>
            <li>Buscar vagas compatíveis com seu perfil</li>
            <li>Adaptar seu currículo para uma vaga específica</li>
            <li>Gerar cartas de apresentação</li>
            <li>Criar um plano de estudos personalizado (📘 Enviar PDF ou digite o tema)</li>
        </ul>
    `, true); // O 'true' informa ao addMessage que é HTML
}

async function sendChatMessage(prompt) {
    addMessage('user', prompt);
    const loading = showBotLoading();
    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const data = await res.json();
        addMessage('bot', data.ia_response || "❌ Erro: Não recebi uma resposta válida.");
    } catch (error) {
        addMessage('bot', `❌ Erro de conexão: ${error.message}`);
    } finally {
        stopThinking();
        elements.chatBox.removeChild(loading);
    }
}

// ==== FLUXO DE ESTUDO ====
function startStudyFlow(subject, pdfFile = null) {
    appState.isStudying = true;
    appState.studySubject = subject;
    appState.studyPdf = pdfFile;
    saveState();
    elements.chatForm.style.display = 'none';
    elements.topicSelector.style.display = 'block';
    
    // No mobile, feche o menu ao iniciar o fluxo
    if (elements.sidebarContainer.classList.contains('mobile-open')) {
        toggleSidebar();
    }
}

async function sendStudyRequest(interest) {
    addMessage('user', `Quero estudar sobre "${appState.studySubject}" com foco em "${interest}".`);
    elements.topicSelector.style.display = 'none';
    elements.chatForm.style.display = 'flex';
    const loading = showBotLoading();

    const formData = new FormData();
    formData.append("subject", appState.studySubject);
    formData.append("interests", JSON.stringify([interest]));
    if (appState.studyPdf) {
        formData.append("pdf", appState.studyPdf, appState.studyPdf.name);
    }

    try {
        const res = await fetch("/api/study", { method: "POST", body: formData });
        const data = await res.json();
        if (data.ok && data.study_plan) {
            addMessage('bot', `<b>📘 Plano de Estudos — Método Paulo Freire:</b><br><br>${data.study_plan}`, true);
        } else {
            addMessage('bot', `❌ Erro ao gerar plano de estudos: ${data.error}`);
        }
    } catch (error) {
        addMessage('bot', `❌ Erro de conexão: ${error.message}`);
    } finally {
        stopThinking();
        elements.chatBox.removeChild(loading);
        appState = { isStudying: false, studySubject: null, studyPdf: null };
        saveState();
    }
}

// ==== FLUXO DE CARREIRA ====
// 1. Upload de CV
elements.uploadCVBtn.onclick = async (e) => {
    elements.cvInput.click();
};
elements.cvInput.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    addMessage('user', `📄 Enviando currículo: ${file.name}`);
    const loading = showBotLoading();
    
    // No mobile, feche o menu
    if (elements.sidebarContainer.classList.contains('mobile-open')) {
        toggleSidebar();
    }

    const formData = new FormData();
    formData.append("cv_file", file);
    
    try {
        const res = await fetch(`/api/upload_cv?user_id=default_user`, { method: "POST", body: formData });
        const data = await res.json();
        if (data.cv_analysis_summary) {
            addMessage('bot', `<b>✅ Currículo processado!</b> Aqui está minha análise como Coach de Carreira:\n\n${data.cv_analysis_summary}`);
        } else {
            addMessage('bot', `❌ Erro no upload: ${data.error}`);
        }
    } catch (error) {
        addMessage('bot', `❌ Erro de conexão: ${error.message}`);
    } finally {
        stopThinking();
        elements.chatBox.removeChild(loading);
    }
};

// 2. Upload de PDF de Estudos
elements.uploadStudyBtn.onclick = () => {
    elements.studyInput.click();
};
elements.studyInput.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    addMessage('user', `📘 Enviando PDF de estudos: ${file.name}`);
    const subject = "Conteúdo do PDF"; 
    addMessage('bot', `Certo! Vou analisar seu PDF. Agora, para personalizar seu estudo...`);
    startStudyFlow(subject, file);
};

// 3. Buscar Vagas (Filtros)
elements.btnBuscarVagas.onclick = () => {
    const prefs = {
        cargo: elements.prefCargo.value,
        cidade: elements.prefCidade.value,
        estado: elements.prefEstado.value,
        modelo: elements.prefModelo.value,
        tipo: elements.prefTipo.value,
    };
    findJobsAPI("/api/find_jobs", prefs, "Buscando vagas com base nos seus filtros...");
};

// 4. Buscar Vagas com Match (IA)
elements.btnBuscarMatch.onclick = () => {
    const prefs = {
        cargo: elements.prefCargo.value || "vaga",
        user_id: "default_user"
    };
    findJobsAPI("/api/match_jobs", prefs, "Buscando vagas com match (IA) no seu currículo...");
};

async function findJobsAPI(endpoint, body, loadingMessage) {
    addMessage('user', loadingMessage);
    const loading = showBotLoading();

    // No mobile, feche o menu
    if (elements.sidebarContainer.classList.contains('mobile-open')) {
        toggleSidebar();
    }
    
    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.ok && data.jobs && data.jobs.length > 0) {
            addMessage('bot', `Encontrei ${data.jobs.length} vagas. Analisando...`);
            data.jobs.forEach(job => renderJobCard(job));
        } else {
            addMessage('bot', `😕 Nenhuma vaga encontrada com esses critérios.`);
        }
    } catch (error) {
        addMessage('bot', `❌ Erro de conexão ao buscar vagas: ${error.message}`);
    } finally {
        stopThinking();
        elements.chatBox.removeChild(loading);
    }
}

function renderJobCard(job) {
    const safeDesc = job.body.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    const safeTitle = job.title.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    const cardHtml = `
        <div class="job-card">
            <h4>${job.title}</h4>
            <p class="job-card-desc">${job.body.substring(0, 150)}...</p>
            <div class="job-card-actions">
                <a href="${job.href}" target="_blank" class="job-btn job-link">Ver Vaga</a>
                <button class="job-btn" data-action="fit" data-desc="${safeDesc}" data-title="${safeTitle}">
                    1. Compatibilidade (IA)
                </button>
                <button class="job-btn" data-action="adapt" data-desc="${safeDesc}" data-title="${safeTitle}">
                    2. Adaptar CV
                </button>
                <button class="job-btn" data-action="cover" data-desc="${safeDesc}" data-title="${safeTitle}">
                    3. Carta de Apresentação
                </button>
            </div>
        </div>
    `;
    addMessage('bot', cardHtml, true);
}


// ==== LÓGICA DO MENU MOBILE ====
function toggleSidebar() {
    const isOpen = elements.sidebarContainer.classList.toggle('mobile-open');
    elements.sidebarOverlay.style.display = isOpen ? 'flex' : 'none';
    elements.sidebarOverlay.classList.toggle('visible', isOpen);
}

elements.openSidebar.onclick = toggleSidebar;
elements.closeSidebar.onclick = toggleSidebar;
elements.sidebarOverlay.onclick = toggleSidebar;


// ==== EVENT LISTENERS GLOBAIS ====
window.addEventListener('DOMContentLoaded', () => {
    loadState();
    const history = localStorage.getItem(CHAT_HISTORY_KEY);
    if (appState.isStudying) {
        loadChatHistory();
        startStudyFlow(appState.studySubject, null);
    } else if (history) {
        elements.welcomeModal.style.display = 'flex';
    } else {
        showWelcomeMessage();
    }
});

elements.continueChatBtn.onclick = () => {
    elements.welcomeModal.style.display = 'none';
    loadChatHistory();
};
elements.startNewChatBtn.onclick = () => {
    elements.welcomeModal.style.display = 'none';
    clearChat();
};
elements.newChatBtn.onclick = clearChat;

elements.chatForm.onsubmit = (e) => {
    e.preventDefault();
    const prompt = elements.chatInput.value.trim();
    if (!prompt) return;
    elements.chatInput.value = '';

    const studyKeywords = ['estudar sobre', 'me ensine', 'preciso estudar', 'tema de estudo'];
    if (studyKeywords.some(kw => prompt.toLowerCase().includes(kw))) {
        const subject = prompt.toLowerCase().replace('estudar sobre', '').replace('me ensine sobre', '').replace('preciso estudar', '').trim();
        addMessage('user', prompt);
        addMessage('bot', `Certo! Vamos estudar sobre "${subject}".`);
        startStudyFlow(subject);
    } else {
        sendChatMessage(prompt);
    }
};

$$('.topic-btn').forEach(btn => {
    btn.onclick = () => {
        const interest = btn.dataset.topic;
        sendStudyRequest(interest);
    };
});
elements.customTopicInput.onkeydown = (e) => {
    if (e.key === 'Enter') {
        const interest = elements.customTopicInput.value.trim();
        if (interest) {
            sendStudyRequest(interest);
            elements.customTopicInput.value = '';
        }
    }
};

elements.chatBox.addEventListener('click', async (e) => {
    if (!e.target.classList.contains('job-btn')) return;
    const action = e.target.dataset.action;
    if (!action) return;

    const job_description = e.target.dataset.desc;
    const job_title = e.target.dataset.title;
    const body = {
        job_description: job_description,
        job_title: job_title,
        user_id: "default_user"
    };

    let endpoint = '';
    let userMessage = '';
    
    if (action === 'fit') {
        endpoint = '/api/job_fit';
        userMessage = `Analisando compatibilidade para: "${job_title}"...`;
    }
    if (action === 'adapt') {
        endpoint = '/api/adapt_cv';
        userMessage = `Adaptando meu CV para: "${job_title}"...`;
    }
    if (action === 'cover') {
        endpoint = '/api/generate_cover_letter';
        userMessage = `Gerando carta de apresentação para: "${job_title}"...`;
    }

    addMessage('user', userMessage);
    const loading = showBotLoading();
    
    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        const responseText = data.analysis || data.adapted_cv || data.cover_letter;
        
        if (responseText) {
            if (action === 'adapt' || action === 'cover') {
                addMessage('bot', `Pronto! Aqui está:\n\n<pre>${responseText}</pre>`, true);
            } else {
                addMessage('bot', responseText, true);
            }
        } else {
            addMessage('bot', `❌ Erro: ${data.error || 'Resposta inválida da API.'}`);
        }
    } catch (error) {
        addMessage('bot', `❌ Erro de conexão: ${error.message}`);
    } finally {
        stopThinking();
        elements.chatBox.removeChild(loading);
    }
});