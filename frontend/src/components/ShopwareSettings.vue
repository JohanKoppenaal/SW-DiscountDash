<template>
  <div class="card">
    <div class="card-body">
      <h5 class="card-title">Shopware Instellingen</h5>

      <form @submit.prevent="saveSettings">
        <div class="mb-3">
          <label class="form-label">Shop URL</label>
          <input
              v-model="settings.shop_url"
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
  name: 'ShopwareSettings',
  data() {
    return {
      settings: {
        shop_url: '',
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
        console.log('Loading settings...')  // Debug log
        const response = await axios.get('http://127.0.0.1:5000/api/get_credentials')
        console.log('Settings response:', response.data)  // Debug log
        if (response.status === 200) {
          this.settings = response.data
        }
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    },
    async saveSettings() {
      this.isSaving = true
      try {
        console.log('Saving settings:', this.settings)  // Debug log
        const response = await axios.post('http://127.0.0.1:5000/api/save_credentials', this.settings, {
          headers: {
            'Content-Type': 'application/json',
          }
        })
        console.log('Save response:', response.data)  // Debug log
        this.$emit('settings-saved')
      } catch (error) {
        console.error('Error saving settings:', error.response?.data || error)
        if (error.response) {
          console.error('Error response:', error.response.data)
          console.error('Error status:', error.response.status)
          console.error('Error headers:', error.response.headers)
        }
        alert('Er ging iets mis bij het opslaan van de instellingen')
      } finally {
        this.isSaving = false
      }
    }
  }
}
</script>