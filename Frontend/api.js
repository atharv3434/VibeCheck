// static/js/api.js — API client

const API = {
    token: () => localStorage.getItem('token'),
    me:    () => JSON.parse(localStorage.getItem('me') || 'null'),
  
    headers(json = true) {
      const h = {}
      const t = this.token()
      if (t) h['Authorization'] = `Bearer ${t}`
      if (json) h['Content-Type'] = 'application/json'
      return h
    },
  
    async request(method, path, body) {
      const opts = { method, headers: this.headers(!body?.append) }
      if (body) opts.body = body?.append ? body : JSON.stringify(body)
      if (body?.append) delete opts.headers['Content-Type']
      const res = await fetch('/api' + path, opts)
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      return data
    },
  
    get:    (path)       => API.request('GET',    path),
    post:   (path, body) => API.request('POST',   path, body),
    put:    (path, body) => API.request('PUT',    path, body),
    delete: (path)       => API.request('DELETE', path),
  
    // Auth
    register: (d) => API.post('/auth/register', d),
    login:    (d) => API.post('/auth/login',    d),
    getMe:    ()  => API.get('/auth/me'),
  
    // Feed
    getFeed:    (offset=0) => API.get(`/feed?limit=10&offset=${offset}`),
    getExplore: (offset=0) => API.get(`/explore?offset=${offset}`),
  
    // Posts
    likePost:    (id)  => API.post(`/posts/${id}/like`),
    getComments: (id)  => API.get(`/posts/${id}/comments`),
    addComment:  (id, text) => API.post(`/posts/${id}/comments`, { text }),
    deletePost:  (id)  => API.delete(`/posts/${id}`),
  
    // Users
    getProfile:  (u)   => API.get(`/users/${u}`),
    followUser:  (u)   => API.post(`/users/${u}/follow`),
    searchUsers: (q)   => API.get(`/users/search?q=${encodeURIComponent(q)}`),
  
    // Stories
    getStories:  ()    => API.get('/stories/feed'),
    viewStory:   (id)  => API.post(`/stories/${id}/view`),
  
    // Notifications
    getNotifs:  ()     => API.get('/notifications'),
    unreadCount: ()    => API.get('/notifications/unread'),
  }
