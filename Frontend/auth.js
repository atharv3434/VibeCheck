// static/js/auth.js
function showAuth() {
    document.getElementById('navbar').classList.add('hidden')
    document.getElementById('view').innerHTML = `
      <div class="auth-page">
        <div class="auth-card">
          <div class="auth-logo">📸 Photogram</div>
          <div class="auth-tabs">
            <button class="auth-tab active" onclick="switchAuthTab('login',this)">Log in</button>
            <button class="auth-tab" onclick="switchAuthTab('register',this)">Sign up</button>
          </div>
          <div id="login-panel">
            <form onsubmit="doLogin(event)">
              <input name="username" placeholder="Username" required autocomplete="username"/>
              <input name="password" type="password" placeholder="Password" required autocomplete="current-password"/>
              <button type="submit" class="btn-primary" id="login-btn">Log In</button>
            </form>
          </div>
          <div id="register-panel" class="hidden">
            <form onsubmit="doRegister(event)">
              <input name="full_name" placeholder="Full Name"/>
              <input name="username" placeholder="Username" required autocomplete="username"/>
              <input name="email" type="email" placeholder="Email" required/>
              <input name="password" type="password" placeholder="Password (6+ chars)" required autocomplete="new-password"/>
              <button type="submit" class="btn-primary" id="register-btn">Sign Up</button>
            </form>
          </div>
        </div>
        <div class="auth-card" style="text-align:center;font-size:14px;color:#8e8e8e">
          📸 Share your moments with the world
        </div>
      </div>`
  }
  
  function switchAuthTab(tab, el) {
    document.querySelectorAll('.auth-tab').forEach(t=>t.classList.remove('active'))
    el.classList.add('active')
    document.getElementById('login-panel').classList.toggle('hidden', tab !== 'login')
    document.getElementById('register-panel').classList.toggle('hidden', tab !== 'register')
  }
  
  async function doLogin(e) {
    e.preventDefault()
    const btn = document.getElementById('login-btn')
    btn.disabled = true; btn.textContent = 'Logging in…'
    const fd = new FormData(e.target)
    try {
      const data = await API.login({ username: fd.get('username'), password: fd.get('password') })
      localStorage.setItem('token', data.token)
      localStorage.setItem('me', JSON.stringify({ id: data.user_id, username: data.username, avatar_url: data.avatar_url, full_name: data.full_name }))
      document.getElementById('navbar').classList.remove('hidden')
      navigate('/')
      pollNotifications()
      toast(`Welcome back, ${data.username}! 👋`, 'success')
    } catch(err) { toast(err.message, 'error') }
    finally { btn.disabled = false; btn.textContent = 'Log In' }
  }
  
  async function doRegister(e) {
    e.preventDefault()
    const btn = document.getElementById('register-btn')
    btn.disabled = true; btn.textContent = 'Creating account…'
    const fd = new FormData(e.target)
    try {
      const data = await API.register({
        username: fd.get('username'), email: fd.get('email'),
        password: fd.get('password'), full_name: fd.get('full_name')
      })
      localStorage.setItem('token', data.token)
      localStorage.setItem('me', JSON.stringify({ id: data.user_id, username: data.username, avatar_url: '/static/img/default_avatar.svg' }))
      document.getElementById('navbar').classList.remove('hidden')
      navigate('/')
      toast('Welcome to Photogram! 📸', 'success')
    } catch(err) { toast(err.message, 'error') }
    finally { btn.disabled = false; btn.textContent = 'Sign Up' }
  }