// main.js —— 依赖 api.js 提供的 apiGet, apiPost, apiDelete, authToken
let currentKbId = null;
let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

if (!authToken) {
    window.location.href = '/login';
}

// 退出
document.getElementById('logoutBtn').addEventListener('click', () => {
    sessionStorage.removeItem('token');
    window.location.href = '/login';
});

// ---------- 文件预览更新 ----------
function updateFilePreview(inputElement) {
    const preview = document.getElementById('fileListPreview');
    if (!preview) return;
    preview.innerHTML = '';
    const files = inputElement.files;
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const tag = document.createElement('span');
        tag.className = 'file-tag';
        tag.innerHTML = `📎 ${file.name} <button data-index="${i}">✕</button>`;
        tag.querySelector('button').addEventListener('click', (e) => {
            e.stopPropagation();
            const dt = new DataTransfer();
            for (let j = 0; j < files.length; j++) {
                if (j !== i) dt.items.add(files[j]);
            }
            inputElement.files = dt.files;
            updateFilePreview(inputElement);
        });
        preview.appendChild(tag);
    }
}

// ---------- 知识库列表 ----------
async function loadKbList() {
    const res = await apiGet('/kbs');
    const list = document.getElementById('kbList');
    list.innerHTML = '';
    res.forEach(kb => {
        const li = document.createElement('li');
        li.textContent = kb.name;
        li.onclick = () => openKb(kb.id);
        list.appendChild(li);
    });
}

document.getElementById('createKbBtn').addEventListener('click', async () => {
    const nameInput = document.getElementById('newKbName');
    const name = nameInput.value.trim();
    if (!name) { alert('请输入知识库名称'); return; }
    const formData = new FormData();
    formData.append('name', name);
    try {
        await apiPost('/kbs', formData);
        nameInput.value = '';
        loadKbList();
    } catch (err) {
        alert(err.detail || '创建失败');
    }
});

// ---------- 打开知识库 ----------
async function openKb(kbId) {
    currentKbId = kbId;
    const workspace = document.getElementById('workspace');
    const template = document.getElementById('kbDetailTemplate');
    const clone = template.content.cloneNode(true);
    workspace.innerHTML = '';
    workspace.appendChild(clone);

    // 绑定事件
    document.querySelector('.btn-delete-kb').addEventListener('click', () => deleteKb(kbId));
    document.getElementById('uploadDocBtn').addEventListener('click', () => uploadDocs(kbId));

    // 提问按钮与输入框
    const askBtn = document.getElementById('askBtn');
    const questionInput = document.getElementById('questionInput');

    // 设置发送按钮初始状态
    askBtn.disabled = true;
    askBtn.addEventListener('click', () => askQuestion(kbId));

    // 输入框事件：控制按钮状态 + 回车发送
    questionInput.addEventListener('input', () => {
        askBtn.disabled = questionInput.value.trim() === '';
    });
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && questionInput.value.trim() !== '') {
            askQuestion(kbId);
        }
    });

    // 文件选择与拖拽
    const docFileInput = document.getElementById('docFileInput');
    if (docFileInput) {
        docFileInput.addEventListener('change', () => updateFilePreview(docFileInput));
    }
    const dropArea = document.getElementById('dropArea');
    if (dropArea) {
        dropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropArea.classList.add('dragover');
        });
        dropArea.addEventListener('dragleave', () => {
            dropArea.classList.remove('dragover');
        });
        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dropArea.classList.remove('dragover');
            const dt = e.dataTransfer;
            if (dt && dt.files.length > 0) {
                docFileInput.files = dt.files;
                updateFilePreview(docFileInput);
            }
        });
    }

    loadDocList(kbId);
    loadDocSelectors(kbId);
}

// ---------- 文档列表 ----------
async function loadDocList(kbId) {
    const docs = await apiGet(`/kbs/${kbId}/documents`);
    const list = document.getElementById('docList');
    list.innerHTML = '';
    docs.forEach(doc => {
        const li = document.createElement('li');
        li.innerHTML = `${doc.filename} <button onclick="deleteDoc(${kbId}, ${doc.id})">删除</button>`;
        list.appendChild(li);
    });
}

// ---------- 文档选择器 ----------
async function loadDocSelectors(kbId) {
    try {
        const docs = await apiGet(`/kbs/${kbId}/documents`);
        const container = document.getElementById('docCheckboxes');
        container.innerHTML = '';
        const selector = document.getElementById('docSelector');
        if (docs.length > 0) {
            selector.style.display = 'block';
            docs.forEach(doc => {
                const label = document.createElement('label');
                label.style.display = 'inline-flex';
                label.style.alignItems = 'center';
                label.style.marginRight = '16px';
                label.style.marginBottom = '8px';
                label.innerHTML = `<input type="checkbox" value="${doc.filename}" checked style="margin-right:6px;"> ${doc.filename}`;
                container.appendChild(label);
            });
        } else {
            selector.style.display = 'none';
        }
    } catch (e) {}
}

function getSelectedDocs() {
    const checks = document.querySelectorAll('#docCheckboxes input[type="checkbox"]:checked');
    return Array.from(checks).map(cb => cb.value);
}

// ---------- 上传文档（多文件）----------
async function uploadDocs(kbId) {
    const fileInput = document.getElementById('docFileInput');
    const files = fileInput.files;
    if (files.length === 0) {
        alert('请先选择文件');
        return;
    }

    const formData = new FormData();
    for (let f of files) {
        formData.append('files', f);
    }

    try {
        const data = await apiPost(`/kbs/${kbId}/upload`, formData);
        alert(data.message);
        fileInput.value = '';
        updateFilePreview(fileInput);
        loadDocList(kbId);
        loadDocSelectors(kbId);
    } catch (err) {
        alert(err.detail || '上传失败');
    }
}

// ---------- 删除文档 ----------
window.deleteDoc = async (kbId, docId) => {
    if (!confirm('确定删除该文档？')) return;
    await apiDelete(`/kbs/${kbId}/documents/${docId}`);
    loadDocList(kbId);
    loadDocSelectors(kbId);
};

// ---------- 删除知识库 ----------
async function deleteKb(kbId) {
    if (!confirm('确定删除该知识库？')) return;
    await apiDelete(`/kbs/${kbId}`);
    currentKbId = null;
    document.getElementById('workspace').innerHTML = '<div class="empty-state">知识库已删除</div>';
    loadKbList();
}

// ---------- 授权用户 ----------
window.authorizeUser = async () => {
    const username = document.getElementById('authorizeUsername').value.trim();
    if (!username) return alert('请输入用户名');
    const formData = new FormData();
    formData.append('username', username);
    try {
        const data = await apiPost(`/kbs/${currentKbId}/authorize`, formData);
        alert(data.message);
        document.getElementById('authModal').style.display = 'none';
    } catch (err) {
        alert(err.detail || '授权失败');
    }
};

// ---------- 问答（带置信度、来源、多轮对话）----------
async function askQuestion(kbId) {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question) return;

    const chatBox = document.getElementById('chatBox');
    chatBox.innerHTML += `<div class="user-msg"><div>🧑 ${question}</div></div>`;
    document.getElementById('askLoading').style.display = 'block';

    const selectedDocs = getSelectedDocs();
    try {
        const data = await apiPost(`/kbs/${kbId}/ask`, {
            question: question,
            documents: selectedDocs.length > 0 ? selectedDocs : null,
            session_id: sessionId,
        });

        let botMsg = data.answer;
        if (data.confidence) {
            botMsg += `\n\n📊 置信度：${data.confidence}`;
        }
        if (data.sources && data.sources.length > 0) {
            botMsg += '\n\n📚 参考来源：\n' + data.sources.map((s, i) =>
                `[${i+1}] ${s.source} ${s.page ? '第'+s.page+'页' : '（全文）'} (相似度: ${s.score.toFixed(3)})`
            ).join('\n');
        }
        chatBox.innerHTML += `<div class="bot-msg"><div>🤖 ${botMsg.replace(/\n/g, '<br>')}</div></div>`;
    } catch (err) {
        chatBox.innerHTML += `<div class="error-msg"><div>❌ ${err.detail || '请求失败'}</div></div>`;
    } finally {
        document.getElementById('askLoading').style.display = 'none';
    }
    input.value = '';
    // 清空后手动触发 input 事件以禁用按钮
    input.dispatchEvent(new Event('input'));
}

// 初始化
loadKbList();