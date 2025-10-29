const $ = sel => document.querySelector(sel);

const log = (role, text) => {
  const div = document.createElement("div");
  div.className = "msg " + role;
  $('#chatlog').appendChild(div);

  if (role === "m") {
    // ✨ IA — renderiza HTML corretamente
    typeWriterHTML(div, text);
  } else {
    // Usuário — texto puro
    div.innerText = text;
  }

  $('#chatlog').scrollTop = $('#chatlog').scrollHeight;
};

// ✨ Efeito de digitação preservando HTML e Markdown
function typeWriterHTML(element, text, speed = 12) {
  // Converte **markdown** simples para <b>
  const html = text
    .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
    .replace(/\n/g, "<br>");

  let i = 0;
  function typing() {
    element.innerHTML = html.slice(0, i);
    i++;
    if (i <= html.length) setTimeout(typing, speed);
  }
  typing();
}

const typingIndicator = $('#typingIndicator');
const showTyping = show => typingIndicator.classList[show ? "remove" : "add"]("hidden");

async function api(path, method = "GET", body = null) {
  const opts = { method, headers: {} };
  if (body && !(body instanceof FormData)) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) opts.body = body;

  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ==========================================
// ✨ Função enviar mensagem
// ==========================================
$('#send').onclick = sendPrompt;
$('#prompt').addEventListener("keypress", e => {
  if (e.key === "Enter") sendPrompt();
});

async function sendPrompt() {
  const uid = $('#userId').value.trim() || 'anon';
  const p = $('#prompt').value.trim();
  if (!p) return;
  log('u', p);
  $('#prompt').value = '';
  showTyping(true);
  try {
    const res = await api('/api/chat', 'POST', { user_id: uid, prompt: p });
    showTyping(false);
    log('m', res.ia_response);
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro: ' + e.message);
  }
}

// ==========================================
// 📄 Upload de Currículo
// ==========================================
$('#btnUpload').onclick = () => $('#cvInput').click();

$('#cvInput').onchange = async (ev) => {
  const uid = $('#userId').value.trim() || 'anon';
  const f = ev.target.files[0];
  if (!f) return;
  const fd = new FormData();
  fd.append('cv_file', f);
  fd.append('user_id', uid);
  log('u', `📄 Enviando currículo: ${f.name}`);
  showTyping(true);
  try {
    const res = await api(`/api/upload_cv?user_id=${uid}`, 'POST', fd);
    showTyping(false);
    log('m', `✅ Currículo processado!\n\n🧩 Resumo: ${res.cv_analysis_summary || res.summary}`);
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro upload: ' + e.message);
  }
};

// ==========================================
// 🔍 Buscar Vagas (com filtros avançados)
// ==========================================
$('#btnBuscar').onclick = async () => {
  const uid = $('#userId').value.trim() || 'anon';
  const area = $('#prefArea').value.trim();
  const estado = $('#prefEstado').value.trim();
  const cidade = $('#prefCidade').value.trim();
  const modelo = $('#prefModelo').value.trim();
  const tipo = $('#prefTipo').value.trim();

  if (!area) return log('m', '⚠️ Preencha o campo "Área desejada" antes de buscar.');

  log('u', `🔍 Buscando vagas para: ${area} (${cidade || estado || 'Brasil'})`);
  showTyping(true);
  try {
    const res = await api('/api/find_jobs', 'POST', {
      user_id: uid,
      job_title: area,
      estado,
      cidade,
      modelo,
      tipo
    });

    showTyping(false);

    if (!res.jobs?.length) return log('m', 'Nenhuma vaga encontrada 😕');

    let msg = `🔍 <b>Vagas encontradas (${area}):</b>\n\n`;
    res.jobs.forEach((j, i) => {
      msg += `
        <div class="vaga-card">
          <b>${j.title}</b><br>
          <p>${j.body || ''}</p>
          <p><b>📍 Local:</b> ${j.local || cidade || estado || 'Brasil'}<br>
             <b>📑 Modelo:</b> ${j.modelo || 'Não informado'}<br>
             <b>💼 Tipo:</b> ${j.tipo || 'Não informado'}</p>
          <a href="${j.href}" target="_blank" class="link-vaga">🌐 Ver vaga</a><br>
          <div class="actions">
            <button onclick="analisarVaga('${j.title}','${j.href}')">Compatibilidade</button>
            <button onclick="adaptarCV('${j.title}','${j.href}')">Adaptar Currículo</button>
            <button onclick="cartaApresentacao('${j.title}','${j.href}')">Carta de Apresentação</button>
          </div>
        </div>
      `;
    });
    log('m', msg);
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro: ' + e.message);
  }
};

// ==========================================
// 💡 Buscar Vagas com Match Automático
// ==========================================
$('#btnMatch').onclick = async () => {
  const uid = $('#userId').value.trim() || 'anon';
  log('u', '💡 Buscando vagas que dão Match comigo...');
  showTyping(true);
  try {
    const estado = $('#prefEstado').value.trim();
const cidade = $('#prefCidade').value.trim();
const modelo = $('#prefModelo').value.trim();
const tipo = $('#prefTipo').value.trim();

const res = await api('/api/match_jobs', 'POST', {
  user_id: uid,
  estado,
  cidade,
  modelo,
  tipo
});

    showTyping(false);

    if (!res.jobs?.length) return log('m', 'Nenhuma vaga compatível 😕');

    let msg = `✨ <b>Vagas que dão Match com você:</b>\n\n`;
    res.jobs.forEach(j => {
      msg += `
        <div class="vaga-card">
          <b>${j.title}</b><br>
          <p>${j.analysis}</p>
          <a href="${j.href}" target="_blank" class="link-vaga">🌐 Ver vaga</a><br>
          <div class="actions">
            <button onclick="analisarVaga('${j.title}','${j.href}')">Compatibilidade</button>
            <button onclick="adaptarCV('${j.title}','${j.href}')">Adaptar Currículo</button>
            <button onclick="cartaApresentacao('${j.title}','${j.href}')">Carta de Apresentação</button>
          </div>
        </div>
      `;
    });
    log('m', msg);
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro: ' + e.message);
  }
};

// ==========================================
// 🧠 Botões das Vagas
// ==========================================
async function analisarVaga(title, href) {
  const uid = $('#userId').value.trim() || 'anon';
  log('u', `📊 Analisar compatibilidade para: ${title}`);
  showTyping(true);
  try {
    const res = await api('/api/job_fit', 'POST', { user_id: uid, job_title: title, job_link: href });
    showTyping(false);
    log('m', res.fit_analysis || res.message || 'Análise concluída!');
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro análise: ' + e.message);
  }
}

async function adaptarCV(title, href) {
  const uid = $('#userId').value.trim() || 'anon';
  log('u', `🧾 Adaptar currículo para: ${title}`);
  showTyping(true);
  try {
    const res = await api('/api/adapt_cv', 'POST', { user_id: uid, job_title: title, job_link: href });
    showTyping(false);
    log('m', res.adapted_cv || res.message || 'Currículo adaptado!');
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro adaptação: ' + e.message);
  }
}

async function cartaApresentacao(title, href) {
  const uid = $('#userId').value.trim() || 'anon';
  log('u', `✉️ Gerar carta de apresentação para: ${title}`);
  showTyping(true);
  try {
    const res = await api('/api/generate_cover_letter', 'POST', { user_id: uid, job_title: title, job_link: href });
    showTyping(false);
    log('m', res.generated_cover_letter || res.message || 'Carta gerada!');
  } catch (e) {
    showTyping(false);
    log('m', '❌ Erro carta: ' + e.message);
  }
}
