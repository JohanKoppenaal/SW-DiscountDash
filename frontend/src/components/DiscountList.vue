<template>
  <div class="card mt-4">
    <div class="card-body">
      <h5 class="card-title">Kortingen Overzicht</h5>

      <!-- Loading state -->
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Laden...</span>
        </div>
        <p class="mt-2">Kortingen worden geladen...</p>
      </div>

      <!-- Error message -->
      <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show" role="alert">
        <span>{{ errorMessage }}</span>
        <button type="button" class="btn btn-sm btn-outline-danger" @click="errorMessage = ''">
          Sluiten
        </button>
      </div>

      <div v-if="!isLoading" class="table-responsive">
        <table class="table">
          <thead>
          <tr>
            <th>Naam</th>
            <th>Korting %</th>
            <th>Aantal Producten</th>
            <th>Voorwaarden</th>
            <th>Acties</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="discount in discounts" :key="discount.id">
            <td>{{ discount.name }}</td>
            <td>{{ discount.percentage }}%</td>
            <td>{{ discount.affected_products }}</td>
            <td>
              <small class="d-block" v-for="(group, index) in discount.conditions" :key="index">
                {{ formatConditionGroup(group) }}
              </small>
            </td>
            <td>
              <button
                  class="btn btn-sm btn-outline-danger"
                  @click="removeDiscount(discount)"
              >
                Verwijderen
              </button>
            </td>
          </tr>
          <tr v-if="discounts.length === 0">
            <td colspan="5" class="text-center py-4">
              Nog geen kortingen aangemaakt
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
  name: 'DiscountList',
  data() {
    return {
      discounts: [],
      manufacturers: [],
      categories: [],
      tags: [],
      isLoading: true,
      errorMessage: ''
    }
  },
  methods: {
    async loadReferenceData() {
      try {
        const [manufacturersRes, categoriesRes, tagsRes] = await Promise.all([
          axios.get('http://127.0.0.1:5000/api/product-manufacturer'),
          axios.get('http://127.0.0.1:5000/api/category'),
          axios.get('http://127.0.0.1:5000/api/tag')
        ]);

        this.manufacturers = manufacturersRes.data.data;
        this.categories = categoriesRes.data.data;
        this.tags = tagsRes.data.data;
      } catch (error) {
        console.error('Error loading reference data:', error);
      }
    },

    async loadDiscounts() {
      this.isLoading = true;
      this.errorMessage = '';
      try {
        await this.loadReferenceData();  // Eerst referentie data laden
        const response = await axios.get('http://127.0.0.1:5000/api/discounts');
        this.discounts = response.data.data;
      } catch (error) {
        console.error('Error loading discounts:', error);
        this.errorMessage = 'Kon kortingen niet laden';
      } finally {
        this.isLoading = false;
      }
    },

    getValueLabel(condition) {
      let item;
      switch (condition.type) {
        case 'manufacturer':
          item = this.manufacturers.find(m => m.id === condition.value);
          return item ? item.name : condition.value;

        case 'category':
          item = this.categories.find(c => c.id === condition.value);
          return item ? item.name : condition.value;

        case 'tag':
          item = this.tags.find(t => t.id === condition.value);
          return item ? item.name : condition.value;

        default:
          return condition.value;
      }
    },

    formatConditionGroup(group) {
      return group.conditions.map(c => {
        const type = {
          manufacturer: 'Merk',
          category: 'Categorie',
          tag: 'Tag'
        }[c.type];
        const operator = c.operator === 'equals' ? 'is' : 'is niet';
        return `${type} ${operator} ${this.getValueLabel(c)}`; // Hier gebruiken we getValueLabel
      }).join(` ${group.operator} `);
    },

    async removeDiscount(discount) {
      if (confirm(`Weet je zeker dat je de korting "${discount.name}" wilt verwijderen?`)) {
        try {
          await axios.delete(`http://127.0.0.1:5001/api/discounts/${discount.id}`);
          await this.loadDiscounts();
        } catch (error) {
          console.error('Error removing discount:', error);
          this.errorMessage = 'Kon korting niet verwijderen';
        }
      }
    }
  },
  mounted() {
    this.loadDiscounts();
  }
}
</script>