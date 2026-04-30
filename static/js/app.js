document.addEventListener('DOMContentLoaded', () => {
    // DOM 元素
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const docListDiv = document.getElementById('docList');
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const loading = document.getElementById('loading');
    const answerText = document.getElementById('answerText');
    const sourcesContainer = document.getElementById('sourcesContainer');

    // 文件拖拽
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
        fileInput.files = e.dataTransfer.files;
        updateFileList();
    });

    fileInput.addEventListener('change', updateFileList);

    function updateFileList() {
        fileList.innerHTML = '';
        Array.from(fileInput.files).forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `
                <span>📎 ${file.name}</span>
                <button onclick="removeFile(${index})">✕</button>
            `;
            fileList.appendChild(div);
        });
    }

    // 移除文件（简化实现，实际需通过 DataTransfer 重新构建 FileList）
    window.removeFile = (index) => {
        const dt = new DataTransfer();
        Array.from(fileInput.files).forEach((file, i) => {
            if (i !== index) dt.items.add(file);
        });
        fileInput.files = dt.files;
        updateFileList();
    };

    // 上传
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
        } catch (err) {
            uploadStatus.innerText = '❌ ' + err.message;
        }
    });

    // 列出文档
    window.listDocuments = async () => {
        const res = await fetch('/documents');
        const data = await res.json();
        if (data.documents.length === 0) {
            docListDiv.innerHTML = '<p>暂无已处理文档</p>';
        } else {
            docListDiv.innerHTML = '<b>已处理文档：</b><br>' +
                data.documents.map(f => `📄 ${f}`).join('<br>');
        }
    };

    // 重置知识库
    window.resetKB = async () => {
        if (!confirm('确定要清空所有知识库内容吗？此操作不可恢复。')) return;
        await fetch('/reset', { method: 'DELETE' });
        uploadStatus.innerText = '知识库已清空';
        docListDiv.innerHTML = '';
    };

    // 提问
    askBtn.addEventListener('click', async () => {
        const question = questionInput.value.trim();
        if (!question) return alert('请输入问题');
        loading.style.display = 'block';
        answerText.innerText = '';
        sourcesContainer.innerHTML = '';

        try {
            const res = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '请求失败');

            answerText.innerText = data.answer;
            // 来源
            if (data.sources.length > 0) {
                let sourcesHtml = '<h3>📚 参考来源</h3>';
                data.sources.forEach((s, i) => {
                    sourcesHtml += `
                        <div class="source-item">
                            <strong>[${i+1}] ${s.source}</strong> ${s.page ? '第'+s.page+'页' : ''}<br>
                            <span>${s.content}</span>
                        </div>`;
                });
                sourcesContainer.innerHTML = sourcesHtml;
            }
        } catch (err) {
            answerText.innerText = '❌ ' + err.message;
        } finally {
            loading.style.display = 'none';
        }
    });
});