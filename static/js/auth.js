document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    try {
        const res = await fetch('/token', { method: 'POST', body: formData });
        if (!res.ok) throw await res.json();
        const data = await res.json();
        sessionStorage.setItem('token', data.access_token);
        window.location.href = '/app';
    } catch (err) {
        document.getElementById('message').innerText = err.detail || '登录失败';
    }
});

document.getElementById('showRegister').addEventListener('click', (e) => {
    e.preventDefault();
    const username = prompt('输入注册用户名');
    const password = prompt('输入密码');
    if (username && password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        fetch('/register', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => alert(data.message || data.detail));
    }
});