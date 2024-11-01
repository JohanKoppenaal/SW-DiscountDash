<template>
  <div class="container py-4">
    <h1 class="mb-4">Shopware Discount Dashboard</h1>

    <!-- Settings button -->
    <div class="mb-4 d-flex justify-content-between align-items-center">
      <div v-if="connectionStatus" class="text-success">
        <span>✓ Verbonden met Shopware</span>
      </div>
      <div v-else-if="connectionStatus === false" class="text-danger">
        <span>✗ Niet verbonden - Controleer instellingen</span>
      </div>
      <button
          class="btn btn-outline-secondary"
          @click="showSettings = true"
      >
        ⚙️ Instellingen
      </button>
    </div>

    <!-- Main Content - Only show when connected -->
    <div v-if="connectionStatus">
      <!-- Navigation Tabs -->
      <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
          <a class="nav-link"
             :class="{ active: activeTab === 'discounts' }"
             href="#"
             @click.prevent="activeTab = 'discounts'">
            Kortingen
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link"
             :class="{ active: activeTab === 'create-discount' }"
             href="#"
             @click.prevent="activeTab = 'create-discount'">
            Nieuwe Korting
          </a>
        </li>
      </ul>

      <!-- Content -->
      <DiscountList v-if="activeTab === 'discounts'" />
      <CreateDiscount v-else-if="activeTab === 'create-discount'" @discount-created="handleDiscountCreated" />
    </div>

    <!-- Show message when not connected -->
    <div v-else-if="connectionStatus === false" class="alert alert-warning">
      Configureer eerst je Shopware instellingen om te beginnen.
    </div>

    <!-- Loading state -->
    <div v-else class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Laden...</span>
      </div>
      <p class="mt-2">Verbinding controleren...</p>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettings" class="modal-wrapper">
      <div class="modal show d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Instellingen</h5>
              <button type="button" class="btn-close" @click="showSettings = false"></button>
            </div>
            <div class="modal-body">
              <ShopwareSettings @settings-saved="handleSettingsSaved" />
            </div>
          </div>
        </div>
      </div>
      <div class="modal-backdrop" @click="showSettings = false"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import DiscountList from './components/DiscountList.vue'
import CreateDiscount from './components/CreateDiscount.vue'
import ShopwareSettings from './components/ShopwareSettings.vue'

export default {
  name: 'App',
  components: {
    DiscountList,
    CreateDiscount,
    ShopwareSettings
  },
  data() {
    return {
      connectionStatus: null, // null = loading, true = connected, false = not connected
      activeTab: 'discounts',
      showSettings: false
    }
  },
  async mounted() {
    await this.checkConnection()
  },
  methods: {
    async checkConnection() {
      try {
        // Eerst credentials ophalen
        const response = await axios.get('http://127.0.0.1:5000/api/get_credentials')
        if (response.status === 200 && response.data) {
          // Test verbinding met Shopware
          const testResponse = await axios.get('http://127.0.0.1:5000/api/test_connection')
          this.connectionStatus = testResponse.data.status === 'success'
        } else {
          this.connectionStatus = false
        }
      } catch (error) {
        console.error('Connection check failed:', error)
        this.connectionStatus = false
      }
    },
    async handleSettingsSaved() {
      this.showSettings = false
      await this.checkConnection()
      if (this.connectionStatus) {
        window.location.reload()
      }
    },
    handleDiscountCreated() {
      this.activeTab = 'discounts'
    }
  }
}
</script>

<style>
.modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1040;
}

.modal {
  z-index: 1050;
}
</style>