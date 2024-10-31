<template>
  <div class="card mt-4">
    <div class="card-body">
      <h5 class="card-title">Producten</h5>

      <!-- Success message -->
      <div v-if="successMessage" class="alert alert-success d-flex justify-content-between align-items-center" role="alert">
        <span>{{ successMessage }}</span>
        <button
            type="button"
            class="btn btn-sm btn-outline-success"
            @click="successMessage = ''"
        >
          Sluiten
        </button>
      </div>

      <!-- Error message -->
      <div v-if="errorMessage" class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
        <span>{{ errorMessage }}</span>
        <button
            type="button"
            class="btn btn-sm btn-outline-danger"
            @click="errorMessage = ''"
        >
          Sluiten
        </button>
      </div>

      <!-- Filters -->
      <div class="mb-4">
        <h6>Filters</h6>
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label">Merk</label>
            <select v-model="filters.manufacturer" class="form-select">
              <option value="">Alle merken</option>
              <option v-for="manufacturer in uniqueManufacturers"
                      :key="manufacturer"
                      :value="manufacturer">
                {{ manufacturer }}
              </option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Categorie</label>
            <select v-model="filters.category" class="form-select">
              <option value="">Alle categorieën</option>
              <option v-for="category in uniqueCategories"
                      :key="category"
                      :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Tag</label>
            <select v-model="filters.tag" class="form-select">
              <option value="">Alle tags</option>
              <option v-for="tag in uniqueTags"
                      :key="tag"
                      :value="tag">
                {{ tag }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Laden...</span>
        </div>
        <p class="mt-2">Producten worden geladen...</p>
      </div>

      <!-- Product table -->
      <div v-if="!isLoading" class="table-responsive">
        <table class="table">
          <thead>
          <tr>
            <th>Naam</th>
            <th>Huidige Prijs</th>
            <th>Van Prijs</th>
            <th>Huidige Korting</th>
            <th>Nieuwe Korting %</th>
            <th>Actie</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="product in products" :key="product.id">
            <td>{{ product.name }}</td>
            <td>€{{ getPriceDisplay(product) }}</td>
            <td>€{{ getListPriceDisplay(product) }}</td>
            <td>
              {{ getCurrentDiscount(product) }}%
            </td>
            <td>
              <input
                  type="number"
                  class="form-control form-control-sm"
                  v-model="product.newDiscount"
                  min="0"
                  max="100"
                  style="width: 100px"
                  :disabled="product.isUpdating"
              >
            </td>
            <td>
              <div class="btn-group">
                <button
                    @click="confirmDiscount(product)"
                    class="btn btn-sm btn-primary me-1"
                    :disabled="product.isUpdating"
                >
                  <span v-if="product.isUpdating" class="spinner-border spinner-border-sm me-1"></span>
                  <span>{{ product.isUpdating ? 'Bezig...' : 'Toepassen' }}</span>
                </button>
                <button
                    v-if="hasDiscount(product)"
                    @click="confirmReset(product)"
                    class="btn btn-sm btn-outline-secondary"
                    :disabled="product.isUpdating"
                >
                  <span>Reset</span>
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  props: {
    connectionData: {
      type: Object,
      required: true
    }
  },
  name: 'ProductList',
  data() {
    return {
      products: [],
      allProducts: [],
      manufacturers: [],
      categories: [],
      tags: [],
      isLoading: true,
      successMessage: '',
      errorMessage: '',
      filters: {
        manufacturer: '',
        category: '',
        tag: ''
      }
    }
  },
  computed: {
    uniqueManufacturers() {
      return this.manufacturers.map(m => m.name).sort();
    },
    uniqueCategories() {
      return this.categories.map(c => c.name).sort();
    },
    uniqueTags() {
      return this.tags.map(t => t.name).sort();
    },
    filteredProducts() {
      return this.allProducts.filter(product => {
        const matchManufacturer = !this.filters.manufacturer ||
            product.manufacturer === this.filters.manufacturer

        const matchCategory = !this.filters.category ||
            (product.categories &&
                product.categories.some(c => c.name === this.filters.category))

        const matchTag = !this.filters.tag ||
            (product.tags &&
                product.tags.some(t => t.name === this.filters.tag))

        return matchManufacturer && matchCategory && matchTag
      })
    }
  },
  watch: {
    filteredProducts: {
      handler(newProducts) {
        this.products = newProducts;
      },
      deep: true
    }
  },
  methods: {
    async loadFilterData() {
      try {
        console.log('Starting to load filter data...');
        const [manufacturersRes, categoriesRes, tagsRes] = await Promise.all([
          axios.get('http://127.0.0.1:5001/api/product-manufacturer'), // Dit was 'manufacturers'
          axios.get('http://127.0.0.1:5001/api/category'),
          axios.get('http://127.0.0.1:5001/api/tag')
        ]);

        console.log('API Responses:', {
          manufacturers: manufacturersRes.data,
          categories: categoriesRes.data,
          tags: tagsRes.data
        });

        this.manufacturers = manufacturersRes.data.data;
        this.categories = categoriesRes.data.data;
        this.tags = tagsRes.data.data;
      } catch (error) {
        console.error('Error loading filter data:', error);
        if (error.response) {
          console.error('Server response:', error.response.data);
        }
        this.errorMessage = error.message || 'Kon filter data niet laden';
      }
    },

    async loadProducts() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const response = await axios.get('http://127.0.0.1:5001/api/products/prices')
        console.log('Raw API response:', response.data.data[0]) // Debug log

        // Filter producten
        const filteredProducts = response.data.data.filter(product => {
          const hasValidPrice = product.price &&
              Array.isArray(product.price) &&
              product.price.length > 0 &&
              product.price[0].gross > 0;

          const isNotChild = !product.parentId;

          return hasValidPrice && isNotChild;
        });

        this.allProducts = filteredProducts.map(product => ({
          ...product,
          newDiscount: 0,
          isUpdating: false
        }));

        // We gebruiken nu filteredProducts computed property
        this.products = this.filteredProducts;

      } catch (error) {
        console.error('Error loading products:', error)
        this.errorMessage = 'Kon producten niet laden. Probeer het later opnieuw.'
      } finally {
        this.isLoading = false
      }
    },

    getCurrentDiscount(product) {
      if (product.price?.[0]?.listPrice?.gross && product.price?.[0]?.gross) {
        const originalPrice = product.price[0].listPrice.gross
        const currentPrice = product.price[0].gross
        const discount = ((originalPrice - currentPrice) / originalPrice) * 100
        return discount.toFixed(1)
      }
      return '0.0'
    },

    getPriceDisplay(product) {
      if (product?.price?.[0]?.gross) {
        return product.price[0].gross.toFixed(2)
      }
      return '0.00'
    },

    getListPriceDisplay(product) {
      if (product?.price?.[0]?.listPrice?.gross) {
        return product.price[0].listPrice.gross.toFixed(2)
      }
      return this.getPriceDisplay(product)
    },

    hasDiscount(product) {
      return product.price?.[0]?.listPrice?.gross > 0;
    },

    async confirmDiscount(product) {
      if (confirm(`Weet je zeker dat je ${product.newDiscount}% korting wilt toepassen op ${product.name}?`)) {
        await this.applyDiscount(product)
      }
    },

    async confirmReset(product) {
      if (confirm(`Weet je zeker dat je de prijs van ${product.name} wilt terugzetten naar de originele prijs?`)) {
        await this.resetPrice(product);
      }
    },

    async applyDiscount(product) {
      product.isUpdating = true
      try {
        const currentPrice = this.getPriceDisplay(product)
        const newPrice = parseFloat(currentPrice) * (1 - (product.newDiscount / 100))

        await axios.patch('http://127.0.0.1:5001/api/products/prices', {
          id: product.id,
          price: newPrice,
          listPrice: parseFloat(currentPrice)
        })

        this.successMessage = `Korting van ${product.newDiscount}% is toegepast op ${product.name}`
        await this.loadProducts()
      } catch (error) {
        console.error('Error applying discount:', error)
        this.errorMessage = `Kon korting niet toepassen op ${product.name}`
      } finally {
        product.isUpdating = false
      }
    },

    async resetPrice(product) {
      product.isUpdating = true
      try {
        const originalPrice = product.price[0].listPrice.gross

        await axios.patch('http://127.0.0.1:5001/api/products/prices', {
          id: product.id,
          price: originalPrice,
          listPrice: null
        })

        this.successMessage = `Prijs van ${product.name} is teruggezet naar origineel`
        await this.loadProducts()
      } catch (error) {
        console.error('Error resetting price:', error)
        this.errorMessage = `Kon de prijs van ${product.name} niet resetten`
      } finally {
        product.isUpdating = false
      }
    }
  },
  async mounted() {
    await Promise.all([
      this.loadProducts(),
      this.loadFilterData()
    ]);
  }
}
</script>

<style scoped>
.alert {
  margin-bottom: 1rem;
}
</style>