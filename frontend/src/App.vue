<template>
  <div class="container py-4">
    <h1 class="mb-4">Shopware Discount Dashboard</h1>

    <!-- Settings button -->
    <div class="mb-4 d-flex justify-content-end">
      <button
          class="btn btn-outline-secondary"
          @click="toggleSettings"
      >
        ⚙️ Instellingen
      </button>
    </div>

    <ShopwareConnect v-if="!isConnected" @connected="handleConnection" />
    <div v-else>
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
        <li class="nav-item">
          <a class="nav-link"
             :class="{ active: activeTab === 'products' }"
             href="#"
             @click.prevent="activeTab = 'products'">
            Producten
          </a>
        </li>
      </ul>

      <!-- Content -->
      <DiscountList v-if="activeTab === 'discounts'" />
      <CreateDiscount v-else-if="activeTab === 'create-discount'" @discount-created="handleDiscountCreated" />
      <ProductList v-else-if="activeTab === 'products'" />
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettings">
      <div class="modal-overlay" @click="toggleSettings">
        <div class="modal-container" @click.stop>
          <div class="modal-content bg-white p-4 rounded">
            <div class="modal-header d-flex justify-content-between align-items-center mb-4">
              <h5 class="modal-title m-0">Instellingen</h5>
              <button type="button" class="btn-close" @click="toggleSettings"></button>
            </div>
            <div class="modal-body">
              <ShopwareSettings @settings-saved="handleSettingsSaved" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ShopwareConnect from './components/ShopwareConnect.vue'
import ProductList from './components/ProductList.vue'
import CreateDiscount from './components/CreateDiscount.vue'
import DiscountList from './components/DiscountList.vue'
import ShopwareSettings from './components/ShopwareSettings.vue'  // Update de import

export default {
  name: 'App',
  components: {
    ShopwareConnect,
    ProductList,
    CreateDiscount,
    DiscountList,
    ShopwareSettings  // Update de component referentie
  },
  data() {
    return {
      isConnected: false,
      activeTab: 'discounts',
      connectionData: null,
      showSettings: false
    }
  },
  methods: {
    handleConnection(data) {
      this.isConnected = true;
      this.connectionData = data;
    },
    handleDiscountCreated() {
      this.activeTab = 'discounts';
    },
    handleSettingsSaved() {  // Removed unused 'settings' parameter
      console.log('Settings saved');
      this.showSettings = false;
      // Optioneel: herlaad de app met nieuwe settings
      window.location.reload();
    },

    toggleSettings() {  // Nieuwe methode
      console.log('Toggling settings:', !this.showSettings);
      this.showSettings = !this.showSettings;
    }
  }
}
</script>

<style>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  width: 100%;
  max-width: 500px;
  margin: 2rem;
  z-index: 1001;
}

.modal-content {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
}
</style>