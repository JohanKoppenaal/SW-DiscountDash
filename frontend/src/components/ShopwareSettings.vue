<template>
  <div class="card">
    <div class="card-body">
      <h5 class="card-title">Shopware Instellingen</h5>

      <form @submit.prevent="saveSettings">
        <div class="mb-3">
          <label class="form-label">Shop URL</label>
          <input
              v-model="settings.url"
              type="text"
              class="form-control"
              required
          >
        </div>

        <div class="mb-3">
          <label class="form-label">Client ID</label>
          <input
              v-model="settings.client_id"
              type="text"
              class="form-control"
              required
          >
        </div>

        <div class="mb-3">
          <label class="form-label">Client Secret</label>
          <input
              v-model="settings.client_secret"
              type="text"
              class="form-control"
              required
          >
        </div>

        <div class="d-flex justify-content-end">
          <button type="submit" class="btn btn-primary" :disabled="isSaving">
            {{ isSaving ? 'Opslaan...' : 'Instellingen Opslaan' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ShopwareSettings',  // Update de component naam
  data() {
    return {
      settings: {
        url: '',
        client_id: '',
        client_secret: ''
      },
      isSaving: false
    }
  },
  async mounted() {
    await this.loadSettings()
  },
  methods: {
    async loadSettings() {
      try {
        const response = await axios.get('http://127.0.0.1:5001/api/credentials')
        if (response.data.status === 'success') {
          this.settings = response.data.data
        }
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    },
    async saveSettings() {
      this.isSaving = true
      try {
        await axios.post('http://127.0.0.1:5001/api/credentials', this.settings)
        this.$emit('settings-saved')
      } catch (error) {
        console.error('Error saving settings:', error)
      } finally {
        this.isSaving = false
      }
    }
  }
}
</script>