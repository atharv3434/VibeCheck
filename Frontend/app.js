// static/js/app.js — SPA router + shared utilities

const ROUTES = { '/': loadFeed, '/explore': loadExplore, '/notifications': loadNotifications, '/profile': loadOwnProfile }

function navigate(path, push = true) {
  if (push) history.pushState({}, '', path)
  const view = document.getElementById('view')
  view.innerHTML = '<div class="spinner"></div>'
  closeAllModals()

  // Profile routes
  if (path.startsWith('/u/')) return loadProfile(path.slice(3))

  const handler = ROUTES[path]
  if (handler) handler()
  else { view.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>Page not found</p></div>' }
}

window.addEventListener('popstate', () => navigate(location.pathname, false))

// ── Auth guard 

function isLoggedIn() { return !!API.token() }

function requireAuth() {
  if (!isLoggedIn()) { showAuth(); return false }
  return true
}

// ── Bootstrap 

window.addEventListener('DOMContentLoaded', async () => {
  if (!isLoggedIn()) { showAuth(); return }
  document.getElementById('navbar').classList.remove('hidden')
  navigate(location.pathname, false)
  pollNotifications()
})

function logout() {
  localStorage.clear()
  document.getElementById('navbar').classList.add('hidden')
  showAuth()
  history.pushState({}, '', '/')
}

// ── Notifications polling 

async function pollNotifications() {
  const updateBadge = async () => {
    try {
      const { count } = await API.unreadCount()
      const badge = document.getElementById('notif-badge')
      if (count > 0) { badge.textContent = count > 9 ? '9+' : count; badge.classList.remove('hidden') }
      else badge.classList.add('hidden')
    } catch {}
  }
  await updateBadge()
  setInterval(updateBadge, 30000)
}

async function loadNotifications() {
  if (!requireAuth()) return
  document.getElementById('view').innerHTML = '<div class="spinner"></div>'
  const { notifications } = await API.getNotifs()
  document.getElementById('notif-badge').classList.add('hidden')

  const types = { like: '❤️ liked your photo', comment: '💬 commented on your photo', follow: '👤 started following you' }
  const ago = (t) => {
    const s = Math.floor(Date.now()/1000 - t)
    if (s < 60) return `${s}s`; if (s < 3600) return `${Math.floor(s/60)}m`
    if (s < 86400) return `${Math.floor(s/3600)}h`; return `${Math.floor(s/86400)}d`
  }

  document.getElementById('view').innerHTML = `
    <h2 style="margin-bottom:16px;font-size:18px;font-weight:600">Notifications</h2>
    <div class="notif-list">
      ${notifications.length ? notifications.map(n => `
        <div class="notif-item ${n.is_read ? '' : 'notif-unread'}"
             onclick="${n.ref_id ? `navigate('/posts/${n.ref_id}')` : `navigate('/u/${n.username}')`}">
          <img src="${n.avatar_url}" onerror="this.src='/static/img/default_avatar.svg'"/>
          <div class="notif-text"><strong>${n.username}</strong> ${types[n.type]||n.type}</div>
          <div class="notif-time">${ago(n.created_at)}</div>
        </div>`).join('') : '<div class="empty-state"><div class="icon">🔔</div><p>No notifications yet</p></div>'}
    </div>`
}

// ── Post modal 

function openNewPost() {
  if (!requireAuth()) return
  document.getElementById('post-modal').classList.remove('hidden')
}

function previewImage(input) {
  const file = input.files[0]; if (!file) return
  const prev = document.getElementById('post-preview')
  document.getElementById('preview-img').src = URL.createObjectURL(file)
  prev.classList.remove('hidden')
}

async function submitPost(e) {
  e.preventDefault()
  const btn = e.target.querySelector('button[type=submit]')
  btn.disabled = true; btn.textContent = 'Sharing…'
  try {
    const fd = new FormData()
    fd.append('file',     document.getElementById('post-file').files[0])
    fd.append('caption',  document.getElementById('post-caption').value)
    fd.append('location', document.getElementById('post-location').value)
    const res = await fetch('/api/posts', { method:'POST', headers:{'Authorization':`Bearer ${API.token()}`}, body:fd })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail)
    toast('Post shared! ✨', 'success')
    closeModal('post-modal')
    e.target.reset()
    document.getElementById('post-preview').classList.add('hidden')
    navigate('/')
  } catch(err) { toast(err.message, 'error') }
  finally { btn.disabled = false; btn.textContent = 'Share Post' }
}

// ── Utilities

function closeModal(id) { document.getElementById(id).classList.add('hidden') }
function closeAllModals() { document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden')) }

function toast(msg, type='info') {
  const el = document.createElement('div')
  el.className = `toast toast-${type}`
  el.textContent = msg
  document.getElementById('toast-container').appendChild(el)
  setTimeout(() => el.remove(), 3000)
}

function timeAgo(ts) {
  const s = Math.floor(Date.now()/1000 - ts)
  if (s < 60) return `${s} seconds ago`
  if (s < 3600) return `${Math.floor(s/60)} minutes ago`
  if (s < 86400) return `${Math.floor(s/3600)} hours ago`
  return `${Math.floor(s/86400)} days ago`
}

function renderHashtags(text) {
  return (text||'').replace(/#(\w+)/g, '<span class="hashtag">#$1</span>')
}

// Search
let searchTimer
function debounceSearch(q) {
  clearTimeout(searchTimer)
  const drop = document.getElementById('search-results')
  if (!q.trim()) { drop.classList.add('hidden'); return }
  searchTimer = setTimeout(async () => {
    const results = await API.searchUsers(q).catch(()=>[])
    drop.innerHTML = results.map(u => `
      <div class="search-item" onclick="navigate('/u/${u.username}');document.getElementById('search-input').value='';document.getElementById('search-results').classList.add('hidden')">
        <img src="${u.avatar_url||'/static/img/default_avatar.svg'}" onerror="this.src='/static/img/default_avatar.svg'"/>
        <div><div class="search-item-name">${u.username}</div><div class="search-item-full">${u.full_name||''}</div></div>
      </div>`).join('') || '<div style="padding:12px;color:#aaa;font-size:13px">No users found</div>'
    drop.classList.remove('hidden')
  }, 300)
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.nav-search')) document.getElementById('search-results').classList.add('hidden')
})

// Post actions (global so inline onclick works)
async function toggleLike(postId, btn) {
  try {
    const { liked } = await API.likePost(postId)
    btn.textContent = liked ? '❤️' : '🤍'
    btn.classList.toggle('liked', liked)
    const card = btn.closest('.post-card')
    const likesEl = card.querySelector('.post-likes')
    const cur = parseInt(likesEl.dataset.count||'0')
    const next = liked ? cur+1 : cur-1
    likesEl.dataset.count = next
    likesEl.textContent = next === 1 ? '1 like' : `${next} likes`
  } catch(e) { toast(e.message,'error') }
}

async function submitComment(e, postId) {
  e.preventDefault()
  const input = e.target.querySelector('input')
  const text  = input.value.trim()
  if (!text) return
  try {
    const c = await API.addComment(postId, text)
    const list = document.querySelector(`#comments-${postId}`)
    const div  = document.createElement('div')
    div.className = 'comment-row'
    div.innerHTML = `<span class="cuser">${c.username}</span>${c.text}`
    list.appendChild(div)
    input.value = ''
  } catch(e) { toast(e.message,'error') }
}

function buildPostCard(p, expanded=false) {
  const me = API.me()
  const isOwn = me && me.id === p.user_id
  return `
  <div class="post-card" id="post-${p.id}">
    <div class="post-header">
      <img src="${p.avatar_url||'/static/img/default_avatar.svg'}"
           onerror="this.src='/static/img/default_avatar.svg'"
           onclick="navigate('/u/${p.username}')"/>
      <div class="post-header-info">
        <div class="post-username" onclick="navigate('/u/${p.username}')">${p.username}</div>
        ${p.location ? `<div class="post-location">${p.location}</div>` : ''}
      </div>
      ${isOwn ? `<button class="post-menu" onclick="if(confirm('Delete post?'))deletePost(${p.id})">⋯</button>` : ''}
    </div>
    <img class="post-img" src="${p.image_url}" loading="lazy" ondblclick="toggleLike(${p.id},document.querySelector('#like-btn-${p.id}'))"/>
    <div class="post-actions">
      <button class="post-action-btn${p.is_liked?' liked':''}" id="like-btn-${p.id}"
              onclick="toggleLike(${p.id},this)">${p.is_liked?'❤️':'🤍'}</button>
      <button class="post-action-btn" onclick="document.querySelector('#comment-input-${p.id}').focus()">💬</button>
      <button class="post-action-btn post-save">🔖</button>
    </div>
    <div class="post-likes" data-count="${p.like_count}">${p.like_count===1?'1 like':`${p.like_count} likes`}</div>
    <div class="post-caption"><span class="post-username">${p.username}</span>${renderHashtags(p.caption)}</div>
    ${!expanded && p.comment_count>0 ? `<div class="post-comments-count" onclick="expandComments(${p.id})">View all ${p.comment_count} comments</div>`:''}
    <div class="post-comments" id="comments-${p.id}">
      ${(p.comments||[]).slice(0,2).map(c=>`<div class="comment-row"><span class="cuser">${c.username}</span>${c.text}</div>`).join('')}
    </div>
    <form class="post-add-comment" onsubmit="submitComment(event,${p.id})">
      <input id="comment-input-${p.id}" placeholder="Add a comment…" autocomplete="off"/>
      <button type="submit" class="comment-submit">Post</button>
    </form>
    <div class="post-time">${timeAgo(p.created_at)}</div>
  </div>`
}

async function expandComments(postId) {
  const comments = await API.getComments(postId)
  const el = document.querySelector(`#comments-${postId}`)
  el.innerHTML = comments.map(c=>`<div class="comment-row"><span class="cuser">${c.username}</span>${c.text}</div>`).join('')
  el.previousElementSibling.remove()
}

async function deletePost(id) {
  try { await API.deletePost(id); document.getElementById(`post-${id}`).remove(); toast('Post deleted','success') }
  catch(e) { toast(e.message,'error') }
}

// Story upload
function openStoryUpload() { document.getElementById('story-upload-modal').classList.remove('hidden') }
async function submitStory(e) {
  e.preventDefault()
  const btn = e.target.querySelector('button[type=submit]')
  btn.disabled = true; btn.textContent = 'Sharing…'
  try {
    const fd = new FormData()
    fd.append('file',    document.getElementById('story-file').files[0])
    fd.append('caption', document.getElementById('story-caption-input').value)
    const res = await fetch('/api/stories', { method:'POST', headers:{'Authorization':`Bearer ${API.token()}`}, body:fd })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail)
    toast('Story shared! 🎬','success')
    closeModal('story-upload-modal')
    e.target.reset()
    navigate('/')
  } catch(err) { toast(err.message,'error') }
  finally { btn.disabled = false; btn.textContent = 'Share Story' }
}
