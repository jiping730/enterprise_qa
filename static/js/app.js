document.addEventListener('DOMContentLoaded', () => {
    // 元素引用
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const loading = document.getElementById('loading');
    const chatBox = document.getElementById('chatBox');
    const docCheckboxes = document.getElementById('docCheckboxes');
    const docSelector = document.getElementById('docSelector');

    // 多轮对话 session_id
    let sessionId = localStorage.getItem('qa_session_id');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('qa_session_id', sessionId);
    }

    // 文件拖拽与选择
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('dragover');
    });
    dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('dragover');
        fileInput.files = e.dataTransfer.files;
        updateFileList();
    });
    fileInput.addEventListener('change', updateFileList);

    function updateFileList() {
        fileList.innerHTML = '';
        Array.from(fileInput.files).forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `<span>📎 ${file.name}</span><button onclick="removeFile(${index})">✕</button>`;
            fileList.appendChild(div);
        });
    }

    // 移除文件（全局函数）
    window.removeFile = (index) => {
        const dt = new DataTransfer();
        Array.from(fileInput.files).forEach((file, i) => {
            if (i !== index) dt.items.add(file);
        });
        fileInput.files = dt.files;
        updateFileList();
    };

    // 上传文件
    uploadBtn.addEventListener('click', async () => {
        if (fileInput.files.length === 0) {
            alert('请先选择文件');
            return;
        }
        uploadStatus.innerText = '正在上传和解析...';
        const formData = new FormData();
        Array.from(fileInput.files).forEach(file => formData.append('files', file));

        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '上传失败');
            uploadStatus.innerText = data.message;
            fileInput.value = '';
            fileList.innerHTML = '';
            loadDocList();   // 刷新文档选择列表
        } catch (err) {
            uploadStatus.innerText = '❌ ' + err.message;
        }
    });

    // 加载文档列表，生成勾选框
    async function loadDocList() {
        try {
            const res = await fetch('/documents');
            const data = await res.json();
            if (data.documents.length > 0) {
                docSelector.style.display = 'block';
                docCheckboxes.innerHTML = data.documents.map(doc =>
                    `<label class="doc-checkbox"><input type="checkbox" value="${doc}" checked> ${doc}</label>`
                ).join('');
            } else {
                docSelector.style.display = 'none';
            }
        } catch (e) {
            console.error('加载文档列表失败:', e);
        }
    }

    // 重置知识库
    window.resetKB = async () => {
        if (!confirm('确定要清空所有知识库内容吗？此操作不可恢复。')) return;
        await fetch('/reset', { method: 'DELETE' });
        uploadStatus.innerText = '知识库已清空';
        docSelector.style.display = 'none';
        loadDocList();
    };

    // 获取选中文档
    function getSelectedDocs() {
        const checks = document.querySelectorAll('#docCheckboxes input[type="checkbox"]:checked');
        return Array.from(checks).map(cb => cb.value);
    }

    // 添加消息到聊天区
    function addMessage(role, text, confidence = '') {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        let innerHTML = `<div class="content">${text.replace(/\n/g, '<br>')}</div>`;
        if (confidence) innerHTML += `<div class="confidence">${confidence}</div>`;
        msgDiv.innerHTML = innerHTML;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // 发送问题
    async function sendQuestion() {
        const question = questionInput.value.trim();
        if (!question) return;
        addMessage('user', question);
        questionInput.value = '';
        loading.style.display = 'block';

        const selectedDocs = getSelectedDocs();
        try {
            const res = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    documents: selectedDocs.length > 0 ? selectedDocs : null,
                    session_id: sessionId
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '请求失败');

            let answerText = data.answer;
            if (data.sources && data.sources.length > 0) {
                answerText += '\n\n📚 参考来源：\n' + data.sources.map((s, i) =>
                    `[${i+1}] ${s.source} ${s.page ? '第'+s.page+'页' : ''} (相似度: ${s.score.toFixed(3)})`
                ).join('\n');
            }
            addMessage('bot', answerText, data.confidence || '');
        } catch (err) {
            addMessage('bot', '❌ ' + err.message);
        } finally {
            loading.style.display = 'none';
        }
    }

    askBtn.addEventListener('click', sendQuestion);
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuestion();
    });

    // 初始加载
    loadDocList();
});