const API_BASE = '';
let authToken = sessionStorage.getItem('token');

async function request(url, options = {}) {
    const headers = { ...options.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(API_BASE + url, { ...options, headers });
    if (res.status === 401) {
        sessionStorage.removeItem('token');
        window.location.href = '/login';
    }
    return res;
}

async function apiGet(url) {
    const res = await request(url);
    if (!res.ok) throw await res.json();
    return res.json();
}

async function apiPost(url, data) {
    const res = await request(url, {
        method: 'POST',
        body: data instanceof FormData ? data : JSON.stringify(data),
    });
    if (!res.ok) throw await res.json();
    return res.json();
}

async function apiDelete(url) {
    const res = await request(url, { method: 'DELETE' });
    if (!res.ok) throw await res.json();
    return res.json();
}