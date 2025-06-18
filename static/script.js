/* =========================================================================
   Combined script.js + auth.js
   -------------------------------------------------------------------------
   Handles:
   1. Supabase-backed auth (login, signup, logout, session storage, redirects)
   2. Code-runner UI (editor, run / clear, status, examples, auto-save, etc.)
   3. API calls with Authorization bearer token when available
   ========================================================================= */

   (() => {
    /* -------------------------------------------------
       🔧  Global DOM look-ups (lazy; may be null)
    ------------------------------------------------- */
    const codeEditor       = document.getElementById('codeEditor');
    const runBtn           = document.getElementById('runBtn');
    const clearBtn         = document.getElementById('clearBtn');
    const output           = document.getElementById('output');
    const statusIndicator  = document.getElementById('statusIndicator');
    const statusDot        = statusIndicator?.querySelector('.status-dot');
    const statusText       = statusIndicator?.querySelector('.status-text');
    const loadingOverlay   = document.getElementById('loadingOverlay');
    const loginForm        = document.getElementById('loginForm');
    const signupForm       = document.getElementById('signupForm');
    const logoutButton     = document.getElementById('logoutButton');
    const usernameDisplay  = document.getElementById('username');
  
    /* -------------------------------------------------
       🌐  API End-points
    ------------------------------------------------- */
    const API_BASE_URL = window.location.origin;    // adapt automatically
    const API_ENDPOINTS = {
      runCode : `${API_BASE_URL}/api/run-code`,
      health  : `${API_BASE_URL}/api/health`,
      login   : `${API_BASE_URL}/api/auth/login`,
      signup  : `${API_BASE_URL}/api/auth/signup`,
      logout  : `${API_BASE_URL}/api/auth/logout`
    };
  
    /* -------------------------------------------------
       🗺️  Auth helpers
    ------------------------------------------------- */
    const getToken = () => localStorage.getItem('token');
    const getUser  = () => JSON.parse(localStorage.getItem('user') || 'null');
  
    const saveSession = ({ token, user }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user',  JSON.stringify(user));
    };
  
    const clearSession = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    };
  
    const isAuthPage = () =>
      window.location.pathname.includes('login.html') ||
      window.location.pathname.includes('signup.html');
  
    /*
     * Redirect logic & nav name
     */
    const syncAuthUI = () => {
      const token = getToken();
      const user  = getUser();
      
      console.log('syncAuthUI - token:', !!token, 'user:', !!user, 'isAuthPage:', isAuthPage());

      if (token && user) {
        console.log('User is authenticated, setting username:', user.email);
        if (usernameDisplay) usernameDisplay.textContent = user.email;
        if (isAuthPage()) {
          console.log('On auth page, redirecting to index.html');
          window.location.replace('index.html');
        }
      } else {
        console.log('User not authenticated');
        if (!isAuthPage()) {
          console.log('Not on auth page, redirecting to login.html');
          window.location.replace('login.html');
        }
      }
    };
  
    /* -------------------------------------------------
       🚀  Code-runner state
    ------------------------------------------------- */
    let isRunning = false;
    let saveTimeout;
  
    /* -------------------------------------------------
       🎬  MAIN: DOMContentLoaded
    ------------------------------------------------- */
    document.addEventListener('DOMContentLoaded', () => {
      syncAuthUI();
  
      /* ------- AUTH: submit handlers ------- */
      loginForm?.addEventListener('submit', handleLogin);
      signupForm?.addEventListener('submit', handleSignup);
      logoutButton?.addEventListener('click', handleLogout);
  
      /* ------- EDITOR: only present on index.html ------- */
      if (codeEditor) {
        runBtn   ?.addEventListener('click', runCode);
        clearBtn ?.addEventListener('click', clearEditor);
        codeEditor.addEventListener('keydown', editorKeydown);
        codeEditor.addEventListener('input', autoResize);
        codeEditor.addEventListener('input', autoSaveCode);
  
        checkApiHealth();
        loadSavedCode();
        autoResize();
      }
    });
  
    /* ========== AUTH HANDLERS ========== */
  
    async function handleLogin(e) {
      e.preventDefault();
      const email    = document.getElementById('email').value;
      const password = document.getElementById('password').value;
  
      console.log('Attempting login for:', email);
  
      try {
        const res  = await fetch(API_ENDPOINTS.login, {
          method : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body   : JSON.stringify({ email, password })
        });
        const data = await res.json();
        console.log('Login response:', data);
        
        if (data.success) {
          console.log('Login successful, saving session...');
          saveSession({
            token : data.session.access_token,
            user  : data.user
          });
          console.log('Session saved, redirecting to index.html...');
          window.location.replace('index.html');
        } else {
          console.log('Login failed:', data.error);
          alert(data.error || 'Login failed');
        }
      } catch (err) {
        console.error('Login error:', err);
        alert('Login failed. Please try again.');
      }
    }
  
    async function handleSignup(e) {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const email    = document.getElementById('email').value;
      const password = document.getElementById('password').value;
  
      try {
        const res  = await fetch(API_ENDPOINTS.signup, {
          method : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body   : JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (data.success) {
          alert('Account created! Please login.');
          window.location.replace('login.html');
        } else {
          alert(data.error || 'Signup failed');
        }
      } catch (err) {
        console.error(err);
        alert('Signup failed. Please try again.');
      }
    }
  
    async function handleLogout() {
      try {
        await fetch(API_ENDPOINTS.logout, {
          method : 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` }
        });
      } catch (_) {
        /* ignore network errors on logout */
      } finally {
        clearSession();
        window.location.replace('login.html');
      }
    }
  
    /* ========== EDITOR & RUNNER ========== */
  
    async function runCode() {
      if (isRunning) return;
      const code = codeEditor.value.trim();
      if (!code) return showError('Please enter some code to run!');
  
      setRunning(true);
      showLoading(true);
  
      try {
        const res = await fetch(API_ENDPOINTS.runCode, {
          method : 'POST',
          headers: {
            'Content-Type' : 'application/json',
            ...(getToken() && { 'Authorization': `Bearer ${getToken()}` })
          },
          body   : JSON.stringify({ code })
        });
  
        const result = await res.json();
        res.ok ? displayResult(result)
               : showError(result.detail || 'Failed to run code');
      } catch (err) {
        console.error(err);
        showError('Network error: Unable to connect to the server');
      } finally {
        setRunning(false);
        showLoading(false);
      }
    }
  
    async function checkApiHealth() {
      try {
        const res = await fetch(API_ENDPOINTS.health);
        res.ok ? setStatus('ready', 'Ready')
               : setStatus('error', 'API Error');
      } catch {
        setStatus('error', 'Offline');
      }
    }
  
    /* ---------- UI helpers ---------- */
  
    function displayResult(res) {
      if (res.success) {
        const content = res.output || 'No output generated';
        const timeStr = `Execution time: ${res.runtime.toFixed(3)} s`;
  
        output.innerHTML =
          `<div class="output-success">${escapeHtml(content)}</div>
           <div class="runtime-info">${timeStr}</div>`;
  
        setStatus('ready', 'Completed');
      } else {
        showError(res.error || 'Unknown error');
      }
    }
  
    function showError(msg) {
      output.innerHTML =
        `<div class="output-error">Error: ${escapeHtml(msg)}</div>`;
      setStatus('error', 'Error');
    }
  
    /* ---------- Running / loading ---------- */
    function setRunning(flag) {
      isRunning = flag;
      if (runBtn) {
        runBtn.disabled = flag;
        runBtn.innerHTML = flag
          ? '<i class="fas fa-spinner fa-spin"></i> Running...'
          : '<i class="fas fa-play"></i> Run Code';
      }
    }
  
    function showLoading(show) {
      loadingOverlay?.classList.toggle('show', show);
    }
  
    function setStatus(type, text) {
      statusDot && (statusDot.className = `status-dot ${type}`);
      statusText && (statusText.textContent = text);
    }
  
    /* ---------- Editor niceties ---------- */
  
    function clearEditor() {
      if (!confirm('Clear the editor?')) return;
      codeEditor.value = '';
      output.innerHTML =
        `<div class="welcome-message">
           <i class="fas fa-info-circle"></i>
           <p>Write your Python code and click "Run Code" to execute it.</p>
         </div>`;
      setStatus('ready', 'Ready');
      autoResize();
      saveCode();
    }
  
    function editorKeydown(e) {
      /* Run (Ctrl/Cmd+Enter) */
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runCode();
      }
      /* Tab indent */
      if (e.key === 'Tab') {
        e.preventDefault();
        insertAtCursor('\t');
      }
    }
  
    function autoResize() {
      codeEditor.style.height = 'auto';
      codeEditor.style.height =
        Math.max(400, codeEditor.scrollHeight) + 'px';
    }
  
    function insertAtCursor(text) {
      const start = codeEditor.selectionStart;
      const end   = codeEditor.selectionEnd;
      const val   = codeEditor.value;
  
      codeEditor.value =
        val.substring(0, start) + text + val.substring(end);
      codeEditor.selectionStart = codeEditor.selectionEnd =
        start + text.length;
      codeEditor.focus();
    }
  
    /* ---------- Local-storage save ---------- */
    const STORAGE_KEY = 'pythonCodeRunner_code';
  
    function saveCode() {
      try {
        localStorage.setItem(STORAGE_KEY, codeEditor.value);
      } catch (err) {
        console.warn('Could not save code:', err);
      }
    }
  
    function loadSavedCode() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) codeEditor.value = saved;
      } catch (err) {
        console.warn('Could not load code:', err);
      }
    }
  
    function autoSaveCode() {
      clearTimeout(saveTimeout);
      saveTimeout = setTimeout(saveCode, 1000);
    }
  
    /* ---------- HTML escape ---------- */
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  
    /* ---------- Visibility & resize ---------- */
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') checkApiHealth();
    });
    window.addEventListener('resize', autoResize);
  
    /* ---------- Example snippets (optional) ---------- */
    // ... (retain addExampleCode / addExampleButtons if desired)
  })();