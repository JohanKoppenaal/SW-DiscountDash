<template>
  <div class="card">
    <div class="card-body">
      <h5 class="card-title">Shopware Verbinding</h5>
      <form @submit.prevent="connect">
        <div class="mb-3">
          <label class="form-label">Shop URL</label>
          <input v-model="credentials.url" type="text" class="form-control" placeholder="http://localhost">
        </div>
        <div class="mb-3">
          <label class="form-label">Client ID</label>
          <input v-model="credentials.client_id" type="text" class="form-control">
        </div>
        <div class="mb-3">
          <label class="form-label">Client Secret</label>
          <input v-model="credentials.client_secret" type="text" class="form-control">
        </div>
        <button type="submit" class="btn btn-primary">Verbinden</button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ShopwareConnect',
  data() {
    return {
      credentials: {
        url: 'http://localhost',
        client_id: 'SWIAWK9TV21VZU9KAHLJQ2HYOA',
        client_secret: 'MTMxNWhKcnBab1YyNWxiN2ZBcDd0WVNkUm85UnlaYWhqcUZVNlI'
      }
    }
  },
  methods: {
    async connect() {
      try {
        const response = await axios.post('http://127.0.0.1:5001/api/connect', this.credentials)
        if (response.data.status === 'success') {
          this.$emit('connected', this.credentials) // Geef credentials door
        }
      } catch (error) {
        console.error('Connection error:', error)
        alert('Kon geen verbinding maken met Shopware')
      }
    }
  }
}
</script>