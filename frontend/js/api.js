/* Thin wrapper around fetch for the JSON API and the streaming chat endpoint. */
const API = (() => {
  const BASE = (window.APP_CONFIG && window.APP_CONFIG.apiBase) || '/api';

  class ApiError extends Error {
    constructor(message, status) { super(message); this.status = status; }
  }

  const NETWORK_MSG = "Can't reach the server. Check your connection and try again.";
  const GENERIC_MSG = 'Something went wrong. Please try again.';

  async function readJson(res) {
    try { return await res.json(); } catch (_) { return null; }
  }

  function handleUnauthorized(path, status) {
    if (status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register') && !path.startsWith('/auth/me')) {
      const here = location.pathname.split('/').pop() + location.search;
      location.href = 'login.html?next=' + encodeURIComponent(here);
    }
  }

  async function request(method, path, body) {
    let res;
    try {
      res = await fetch(BASE + path, {
        method, credentials: 'include',
        headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch (_) {
      throw new ApiError(NETWORK_MSG, 0);
    }
    const data = await readJson(res);
    if (!res.ok || !data || data.success === false) {
      handleUnauthorized(path, res.status);
      throw new ApiError((data && data.error) || GENERIC_MSG, res.status);
    }
    return data.data;
  }

  /* POST that answers with server-sent events. Calls onEvent(obj) for every event. */
  async function stream(path, body, onEvent, signal) {
    let res;
    try {
      res = await fetch(BASE + path, {
        method: 'POST', credentials: 'include', signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    } catch (e) {
      if (e.name === 'AbortError') throw e;
      throw new ApiError(NETWORK_MSG, 0);
    }
    if (!res.ok) {
      const data = await readJson(res);
      handleUnauthorized(path, res.status);
      throw new ApiError((data && data.error) || GENERIC_MSG, res.status);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          if (!frame.startsWith('data: ')) continue;
          let event;
          try { event = JSON.parse(frame.slice(6)); } catch (_) { continue; }
          onEvent(event);
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') throw e;
      throw new ApiError('The connection dropped while I was replying. Please retry.', 0);
    } finally {
      try { reader.releaseLock(); } catch (_) { /* already released */ }
    }
  }

  return {
    ApiError,
    get: (p) => request('GET', p),
    post: (p, b) => request('POST', p, b === undefined ? {} : b),
    put: (p, b) => request('PUT', p, b),
    del: (p) => request('DELETE', p),
    stream,
  };
})();
