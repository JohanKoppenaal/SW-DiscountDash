<template>
  <div class="card mt-4">
    <div class="card-body">
      <h5 class="card-title">Nieuwe Korting Aanmaken</h5>

      <!-- Success/Error messages -->
      <div v-if="successMessage" class="alert alert-success d-flex justify-content-between align-items-center" role="alert">
        <span>{{ successMessage }}</span>
        <button type="button" class="btn btn-sm btn-outline-success" @click="successMessage = ''">
          Sluiten
        </button>
      </div>

      <div v-if="errorMessage" class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
        <span>{{ errorMessage }}</span>
        <button type="button" class="btn btn-sm btn-outline-danger" @click="errorMessage = ''">
          Sluiten
        </button>
      </div>

      <!-- Basic Information -->
      <div class="mb-4">
        <h6>Basis Informatie</h6>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Naam van de korting*</label>
            <input
                v-model="discountData.name"
                type="text"
                class="form-control"
                placeholder="bijv. Zomer Sale 2024"
            >
          </div>
          <div class="col-md-6">
            <label class="form-label">Korting percentage*</label>
            <input
                v-model="discountData.percentage"
                type="number"
                class="form-control"
                min="0"
                max="100"
                placeholder="bijv. 20"
            >
          </div>
        </div>
      </div>

      <!-- Conditions -->
      <div class="mb-4">
        <h6>Voorwaarden</h6>
        <div class="mb-3">
          <label class="form-label d-flex justify-content-between">
            <span>Condities</span>
            <button @click="addConditionGroup" class="btn btn-sm btn-outline-primary">
              + Conditie Groep
            </button>
          </label>

          <!-- Condition Groups -->
          <div v-for="(group, groupIndex) in discountData.conditions" :key="groupIndex" class="card mb-3">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <select v-model="group.operator" class="form-select w-auto">
                  <option value="AND">Alle voorwaarden (AND)</option>
                  <option value="OR">Een van de voorwaarden (OR)</option>
                </select>
                <button @click="removeConditionGroup(groupIndex)" class="btn btn-sm btn-outline-danger">
                  Verwijder Groep
                </button>
              </div>

              <!-- Conditions within group -->
              <div v-for="(condition, condIndex) in group.conditions" :key="condIndex" class="mb-2">
                <div class="row g-2 align-items-center">
                  <div class="col-md-3">
                    <select v-model="condition.type" class="form-select">
                      <option value="manufacturer">Merk</option>
                      <option value="category">Categorie</option>
                      <option value="tag">Tag</option>
                    </select>
                  </div>
                  <div class="col-md-3">
                    <select v-model="condition.operator" class="form-select">
                      <option value="equals">Is gelijk aan</option>
                      <option value="not_equals">Is niet gelijk aan</option>
                    </select>
                  </div>
                  <div class="col-md-4">
                    <select v-model="condition.value" class="form-select">
                      <option value="">Selecteer waarde</option>
                      <option
                          v-for="option in getOptionsForType(condition.type)"
                          :key="option.id"
                          :value="option.id"
                      >
                        {{ option.name }}
                      </option>
                    </select>
                  </div>
                  <div class="col-md-2">
                    <button @click="removeCondition(groupIndex, condIndex)" class="btn btn-sm btn-outline-danger">
                      Verwijder
                    </button>
                  </div>
                </div>
              </div>

              <button @click="addCondition(groupIndex)" class="btn btn-sm btn-outline-secondary mt-2">
                + Voorwaarde Toevoegen
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview -->
      <div class="mb-4">
        <h6>Voorvertoning</h6>
        <div class="alert alert-info">
          <p class="mb-1"><strong>Aantal matchende producten:</strong> {{ matchingProductsCount }}</p>
          <p class="mb-0"><small>Deze korting zal worden toegepast op producten die voldoen aan de bovenstaande voorwaarden.</small></p>
        </div>
      </div>

      <!-- Actions -->
      <div class="d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="resetForm">Annuleren</button>
        <button
            class="btn btn-primary"
            @click="createDiscount"
            :disabled="!isFormValid || isCreating"
        >
          <span v-if="isCreating" class="spinner-border spinner-border-sm me-1"></span>
          {{ isCreating ? 'Bezig met aanmaken...' : 'Korting Aanmaken' }}
        </button>
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
  name: 'CreateDiscount',
  data() {
    return {
      manufacturers: [],
      categories: [],
      tags: [],
      successMessage: '',
      errorMessage: '',
      isCreating: false,
      matchingProductsCount: 0,
      discountData: {
        name: '',
        percentage: null,
        conditions: [
          {
            operator: 'AND',
            conditions: [
              {
                type: 'manufacturer',
                operator: 'equals',
                value: ''
              }
            ]
          }
        ]
      }
    }
  },
  computed: {
    isFormValid() {
      return (
          this.discountData.name &&
          this.discountData.percentage &&
          this.discountData.percentage > 0 &&
          this.discountData.percentage <= 100 &&
          this.discountData.conditions.length > 0 &&
          this.discountData.conditions.every(group =>
              group.conditions.length > 0 &&
              group.conditions.every(c => c.value)
          )
      )
    }
  },
  watch: {
    'discountData.conditions': {
      deep: true,
      handler(newConditions) {
        // Check of er minimaal één conditie is met een waarde
        const hasValues = newConditions.some(group =>
            group.conditions.some(condition => condition.value && condition.value !== '')
        );

        if (hasValues) {
          this.updateMatchingProducts();
        } else {
          this.matchingProductsCount = 0;
        }
      }
    }
  },
  methods: {
    getOptionsForType(type) {
      switch(type) {
        case 'manufacturer':
          return this.manufacturers;
        case 'category':
          return this.categories;
        case 'tag':
          return this.tags;
        default:
          return [];
      }
    },

    async loadFilterData() {
      try {
        console.log('Starting to load filter data...');
        const [manufacturersRes, categoriesRes, tagsRes] = await Promise.all([
          axios.get('http://127.0.0.1:5000/api/product-manufacturer'),
          axios.get('http://127.0.0.1:5000/api/category'),
          axios.get('http://127.0.0.1:5000/api/tag')
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

    addConditionGroup() {
      this.discountData.conditions.push({
        operator: 'AND',
        conditions: [
          {
            type: 'manufacturer',
            operator: 'equals',
            value: ''
          }
        ]
      });
    },

    removeConditionGroup(groupIndex) {
      this.discountData.conditions.splice(groupIndex, 1);
      if (this.discountData.conditions.length === 0) {
        this.addConditionGroup();
      }
    },

    addCondition(groupIndex) {
      this.discountData.conditions[groupIndex].conditions.push({
        type: 'manufacturer',
        operator: 'equals',
        value: null
      });
    },

    removeCondition(groupIndex, condIndex) {
      this.discountData.conditions[groupIndex].conditions.splice(condIndex, 1);
      if (this.discountData.conditions[groupIndex].conditions.length === 0) {
        this.removeConditionGroup(groupIndex);
      }
    },

    resetForm() {
      this.discountData = {
        name: '',
        percentage: null,
        conditions: [
          {
            operator: 'AND',
            conditions: [
              {
                type: 'manufacturer',
                operator: 'equals',
                value: ''
              }
            ]
          }
        ]
      };
      this.successMessage = '';
      this.errorMessage = '';
    },

    async updateMatchingProducts() {
      // Check of er geldige condities zijn
      const hasValidConditions = this.discountData.conditions.some(group =>
          group.conditions.some(condition => condition.value && condition.value !== '')
      );

      if (!hasValidConditions) {
        this.matchingProductsCount = 0;
        return;
      }

      try {
        const response = await axios.post('http://127.0.0.1:5000/api/preview-matching-products', {
          conditions: this.discountData.conditions
        });
        this.matchingProductsCount = response.data.count;
      } catch (error) {
        console.error('Error getting matching products:', error);
      }
    },

    async createDiscount() {
      this.isCreating = true;
      try {
        console.log('Creating discount with data:', this.discountData); // Debug log
        const response = await axios.post('http://127.0.0.1:5000/api/discounts', {
          name: this.discountData.name,
          percentage: parseFloat(this.discountData.percentage),
          conditions: this.discountData.conditions
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log('Response:', response.data); // Debug log

        this.successMessage = 'Korting succesvol aangemaakt!';
        this.$emit('discount-created');
        this.resetForm();
      } catch (error) {
        console.error('Error creating discount:', error);
        if (error.response) {
          console.error('Error response:', error.response.data);
          console.error('Error status:', error.response.status);
        }
        this.errorMessage = error.response?.data?.message || 'Kon de korting niet aanmaken';
      } finally {
        this.isCreating = false;
      }
    }
  },

  async mounted() {
    await this.loadFilterData();
  }
}
</script>