import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database import get_db


class ShopwareService:
    _instance = None

    def __new__(cls):
            if cls._instance is None:
                cls._instance = super(ShopwareService, cls).__new__(cls)
                # Initialize instance attributes
                cls._instance.access_token = None
                cls._instance.base_url = None
                cls._instance.client_id = None
                cls._instance.client_secret = None
                cls._instance.token_expires_at = None
            return cls._instance

    def __init__(self):
        # Deze init wordt elke keer aangeroepen
        if not hasattr(self, 'initialized'):
            self._load_credentials()
            self.initialized = True

    def _load_credentials(self):
        with get_db() as db:
            creds = db.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1").fetchone()
            if creds:
                self.base_url = creds['shop_url']
                self.client_id = creds['client_id']
                self.client_secret = creds['client_secret']

    def save_credentials(self, url, client_id, client_secret):
        with get_db() as db:
            db.execute(
                "INSERT INTO credentials (shop_url, client_id, client_secret) VALUES (?, ?, ?)",
                (url, client_id, client_secret)
            )
            db.commit()
        self._load_credentials()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShopwareService, cls).__new__(cls)
            # Initialize instance attributes
            cls._instance.access_token = None
            cls._instance.base_url = None
            cls._instance.client_id = None
            cls._instance.client_secret = None
            cls._instance.token_expires_at = None
        return cls._instance

    def test_connection(self, url: str, client_id: str, client_secret: str) -> bool:
        """Test connection to Shopware with provided credentials"""
        self.base_url = url
        self.client_id = client_id
        self.client_secret = client_secret

        try:
            success = self.ensure_token()
            return success
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

    def ensure_token(self) -> bool:
        """Ensure we have a valid token, refresh if needed"""
        # Check if token is expired or about to expire
        if self.token_expires_at and datetime.now() < self.token_expires_at - timedelta(minutes=5):
            return True

        try:
            response = requests.post(
                f"{self.base_url}/api/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                # Set token expiry (usually 10 minutes for Shopware, we'll set it to 9 to be safe)
                self.token_expires_at = datetime.now() + timedelta(minutes=9)
                return True
            else:
                print(f"Token refresh failed: {response.text}")
                return False

        except Exception as e:
            print(f"Token refresh failed: {str(e)}")
            return False

    def get_product_prices(self, product_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Get current prices for products"""
        if not self.ensure_token():
            raise Exception("Could not authenticate with Shopware")

        try:
            # Als er specifieke product IDs zijn, halen we alleen die op
            url = f"{self.base_url}/api/product"
            if product_ids and len(product_ids) == 1:
                url = f"{url}/{product_ids[0]}"
            elif product_ids:
                # TODO: Implementeer filter voor meerdere producten
                pass

            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
                return [data]  # Single product response
            else:
                print(f"API Response: {response.text}")
                raise Exception(f"Error fetching product prices: {response.status_code}")

        except Exception as e:
            print(f"Error getting product prices: {str(e)}")
            raise

    def update_product_prices(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.ensure_token():
            raise Exception("Could not authenticate with Shopware")

        try:
            results = []
            for update in updates:
                price_data = {
                    "price": [{
                        "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",  # Default EUR currency ID
                        "gross": update['price'],
                        "net": update['price'] / 1.21,  # BTW berekening (21%)
                        "linked": True
                    }]
                }

                # Alleen listPrice toevoegen als die niet null is
                if update.get('listPrice') is not None:
                    price_data["price"][0]["listPrice"] = {
                        "gross": update['listPrice'],
                        "net": update['listPrice'] / 1.21,
                        "linked": True
                    }

                response = requests.patch(
                    f"{self.base_url}/api/product/{update['id']}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json=price_data
                )

                if response.status_code in [200, 204]:
                    print(f"Successfully updated price for product {update['id']}")
                    results.append({
                        'id': update['id'],
                        'status': 'success'
                    })
                else:
                    print(f"Failed to update price for product {update['id']}: {response.text}")
                    results.append({
                        'id': update['id'],
                        'status': 'error',
                        'message': response.text
                    })

            return results

        except Exception as e:
            print(f"Error updating product prices: {str(e)}")
            raise

    def restore_product_prices(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Restore original prices for products by removing discounts"""
        if not self.ensure_token():
            raise Exception("Could not authenticate with Shopware")

        results = []
        try:
            for product_id in product_ids:
                print(f"Restoring price for product {product_id}")  # Debug log

                # Eerst huidige product data ophalen
                response = requests.get(
                    f"{self.base_url}/api/product/{product_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    }
                )

                if response.status_code != 200:
                    print(f"Failed to get product {product_id}: {response.text}")
                    continue

                product = response.json().get('data')
                if not product or not product.get('price'):
                    print(f"Invalid product data for {product_id}")
                    continue

                price_data = product['price'][0]
                if not price_data.get('listPrice'):
                    print(f"No list price found for product {product_id}, skipping")
                    continue

                original_price = price_data['listPrice']['gross']
                print(f"Found original price {original_price} for product {product_id}")

                # Update price to original and remove listPrice
                update_response = requests.patch(
                    f"{self.base_url}/api/product/{product_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={
                        "price": [{
                            "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",  # Default EUR
                            "gross": original_price,
                            "net": original_price / 1.21,  # BTW berekening
                            "linked": True,
                            "listPrice": None  # Remove listPrice
                        }]
                    }
                )

                if update_response.status_code in [200, 204]:
                    print(f"Successfully restored price for product {product_id}")
                    results.append({
                        'id': product_id,
                        'status': 'success',
                        'original_price': original_price
                    })
                else:
                    print(f"Failed to restore price for product {product_id}: {update_response.text}")
                    results.append({
                        'id': product_id,
                        'status': 'error',
                        'message': update_response.text
                    })

            return results

        except Exception as e:
            print(f"Error in restore_product_prices: {str(e)}")
            raise

    def get_manufacturers(self):
            """Get all manufacturers from Shopware"""
            if not self.ensure_token():
                raise Exception("Could not authenticate with Shopware")

            try:
                response = requests.get(
                    f"{self.base_url}/api/product-manufacturer",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    }
                )

                print(f"Manufacturer response status: {response.status_code}")  # Debug log
                if response.status_code != 200:
                    print(f"Error response: {response.text}")  # Debug log

                if response.status_code == 200:
                    data = response.json()
                    # Map de data naar het formaat dat we willen
                    return [{
                        "id": item["id"],
                        "name": item["name"]
                    } for item in data.get("data", [])]
                else:
                    raise Exception(f"Error fetching manufacturers: {response.status_code}")

            except Exception as e:
                print(f"Error getting manufacturers: {str(e)}")
                raise

    def get_categories(self):
            """Get all categories from Shopware"""
            if not self.ensure_token():
                raise Exception("Could not authenticate with Shopware")

            try:
                response = requests.get(
                    f"{self.base_url}/api/category",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    # Filter alleen actieve categorieën en map naar gewenst formaat
                    return [{
                        "id": item["id"],
                        "name": item["name"]
                    } for item in data.get("data", []) if item.get("active", True)]
                else:
                    raise Exception(f"Error fetching categories: {response.status_code}")

            except Exception as e:
                print(f"Error getting categories: {str(e)}")
                raise

    def get_tags(self):
            """Get all tags from Shopware"""
            if not self.ensure_token():
                raise Exception("Could not authenticate with Shopware")

            try:
                response = requests.get(
                    f"{self.base_url}/api/tag",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return [{
                        "id": item["id"],
                        "name": item["name"]
                    } for item in data.get("data", [])]
                else:
                    raise Exception(f"Error fetching tags: {response.status_code}")

            except Exception as e:
                print(f"Error getting tags: {str(e)}")
                raise

    def ensure_token(self) -> bool:
        """Ensure we have a valid token, refresh if needed"""
        print(f"Checking token status - URL: {self.base_url}, Client ID exists: {bool(self.client_id)}")  # Debug log

        # Check if token is expired or about to expire
        if self.token_expires_at and datetime.now() < self.token_expires_at - timedelta(minutes=5):
            print("Using existing token")  # Debug log
            return True

        try:
            print("Getting new token...")  # Debug log
            response = requests.post(
                f"{self.base_url}/api/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )

            print(f"Token response status: {response.status_code}")  # Debug log
            if response.status_code != 200:
                print(f"Token response error: {response.text}")  # Debug log

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.token_expires_at = datetime.now() + timedelta(minutes=9)
                print("Successfully obtained new token")  # Debug log
                return True
            else:
                print(f"Token refresh failed: {response.text}")  # Debug log
                return False

        except Exception as e:
            print(f"Token refresh failed with exception: {str(e)}")  # Debug log
            return False

    def get_matching_products(self, conditions: List[Dict]) -> List[Dict]:
        """Get products matching the given conditions"""
        if not self.ensure_token():
            raise Exception("Could not authenticate with Shopware")

        try:
            query_params = self._build_query_from_conditions(conditions)
            print("Sending search request with params:", query_params)  # Debug log

            response = requests.post(
                f"{self.base_url}/api/search/product",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "limit": 500,
                    "page": 1,
                    "filter": query_params['filter'],
                    "associations": query_params['associations']
                }
            )

            print(f"Search response status: {response.status_code}")  # Debug log
            if response.status_code != 200:
                print(f"Search response error: {response.text}")  # Debug log

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                raise Exception(f"Error fetching matching products: {response.text}")

        except Exception as e:
            print(f"Error getting matching products: {str(e)}")
            raise

    def _build_query_from_conditions(self, conditions: List[Dict]) -> Dict:
        """Convert frontend conditions to Shopware API query"""
        print("Building query from conditions:", conditions)  # Debug log

        query = {
            "filter": [],
            "associations": {
                "categories": {},
                "tags": {},
                "manufacturer": {}
            }
        }

        for group in conditions:
            group_filters = []
            for condition in group.get('conditions', []):
                print(f"Processing condition: {condition}")  # Debug log

                if not condition.get('value'):
                    print(f"Skipping condition without value: {condition}")
                    continue

                if condition['type'] == 'manufacturer':
                    filter_item = {
                        "type": "equals",
                        "field": "product.manufacturerId",
                        "value": condition['value']
                    }
                    group_filters.append(filter_item)
                    print(f"Added manufacturer filter: {filter_item}")  # Debug log

                elif condition['type'] == 'category':
                    filter_item = {
                        "type": "equals",
                        "field": "product.categoryTree",
                        "value": condition['value']
                    }
                    group_filters.append(filter_item)
                    print(f"Added category filter: {filter_item}")  # Debug log

                elif condition['type'] == 'tag':
                    filter_item = {
                        "type": "contains",
                        "field": "product.tagIds",
                        "value": [condition['value']]
                    }
                    group_filters.append(filter_item)
                    print(f"Added tag filter: {filter_item}")  # Debug log

            if group_filters:  # Only add if there are valid filters
                if group.get('operator') == 'OR' and len(group_filters) > 1:
                    query['filter'].append({
                        "type": "multi",
                        "operator": "OR",
                        "queries": group_filters
                    })
                else:
                    query['filter'].extend(group_filters)

        print("Final query:", query)  # Debug log
        return query

    def create_discount(self, name: str, percentage: float, conditions: List[Dict]) -> Dict:
        """Create a new discount and apply it to matching products"""
        try:
            print(f"Creating discount '{name}' with {percentage}% discount")  # Debug log

            # Eerst alle matchende producten ophalen
            matching_products = self.get_matching_products(conditions)
            print(f"Found {len(matching_products)} matching products")  # Debug log

            # Voor elk matching product de korting toepassen
            results = []
            for product in matching_products:
                try:
                    current_price = product['price'][0]['gross']
                    new_price = current_price * (1 - (percentage / 100))

                    update_result = self.update_product_prices([{
                        'id': product['id'],
                        'price': new_price,
                        'listPrice': current_price
                    }])

                    results.extend(update_result)
                    print(f"Updated price for product {product['id']}: {current_price} -> {new_price}")  # Debug log

                except Exception as e:
                    print(f"Error updating product {product['id']}: {str(e)}")  # Debug log
                    continue

            return {
                'name': name,
                'percentage': percentage,
                'affected_products': len(results),
                'results': results
            }

        except Exception as e:
            print(f"Error in create_discount: {str(e)}")  # Debug log
            raise