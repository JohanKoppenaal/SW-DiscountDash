from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.discount import Discount, Session as DBSession
from .shopware import ShopwareService

class DiscountService:
    def __init__(self):
        self.shopware_service = ShopwareService()
        self.db = DBSession()

    def create_discount(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new discount and apply it to matching products"""
        try:
            # Get matching products to count them
            matching_products = self.shopware_service.get_matching_products(data['conditions'])
            print(f"Found {len(matching_products)} matching products")  # Debug log

            # Create discount record
            discount = Discount(
                name=data['name'],
                percentage=float(data['percentage']),
                conditions=data['conditions'],
                affected_products=len(matching_products)
            )

            # Save to database
            self.db.add(discount)
            self.db.commit()

            # Apply discount to products
            results = []
            for product in matching_products:
                try:
                    # Safely get price data
                    if not product.get('price') or not product['price']:
                        print(f"Skipping product {product.get('id', 'unknown')} - no price data")
                        continue

                    price_data = product['price'][0] if isinstance(product['price'], list) else None
                    if not price_data or 'gross' not in price_data:
                        print(f"Skipping product {product.get('id', 'unknown')} - invalid price structure")
                        continue

                    current_price = price_data['gross']
                    new_price = current_price * (1 - (float(data['percentage']) / 100))

                    update_result = self.shopware_service.update_product_prices([{
                        'id': product['id'],
                        'price': new_price,
                        'listPrice': current_price
                    }])

                    results.extend(update_result)

                except Exception as product_error:
                    print(f"Error processing product {product.get('id', 'unknown')}: {str(product_error)}")
                    continue

            return {
                'id': discount.id,
                'name': discount.name,
                'percentage': discount.percentage,
                'affected_products': len(results)
            }

        except Exception as e:
            self.db.rollback()
            print(f"Error in create_discount: {str(e)}")  # Debug log
            raise

        finally:
            self.db.close()

    def get_discounts(self) -> List[Dict[str, Any]]:
        """Get all discounts with resolved names"""
        try:
            discounts = self.db.query(Discount).order_by(Discount.created_at.desc()).all()

            # Format discounts with resolved names
            formatted_discounts = []
            for discount in discounts:
                formatted_discount = {
                    'id': discount.id,
                    'name': discount.name,
                    'percentage': discount.percentage,
                    'affected_products': discount.affected_products,
                    'created_at': discount.created_at.isoformat() if discount.created_at else None,
                    'conditions': []
                }

                # Resolve names for each condition
                for group in discount.conditions:
                    formatted_group = {
                        'operator': group['operator'],
                        'conditions': []
                    }

                    for condition in group['conditions']:
                        # Get name based on type and ID
                        name = self._get_name_for_condition(condition)

                        formatted_condition = {
                            'type': condition['type'],
                            'operator': condition['operator'],
                            'value': condition['value'],
                            'name': name  # Add resolved name
                        }
                        formatted_group['conditions'].append(formatted_condition)

                    formatted_discount['conditions'].append(formatted_group)

                formatted_discounts.append(formatted_discount)

            return formatted_discounts

        except Exception as e:
            print(f"Error in get_discounts: {str(e)}")
            raise

    def _get_name_for_condition(self, condition: Dict) -> str:
        """Get name for a condition value based on its type"""
        try:
            if condition['type'] == 'manufacturer':
                response = self.shopware_service.get_manufacturers()
                manufacturers = {m['id']: m['name'] for m in response}
                return manufacturers.get(condition['value'], condition['value'])

            elif condition['type'] == 'category':
                response = self.shopware_service.get_categories()
                categories = {c['id']: c['name'] for c in response}
                return categories.get(condition['value'], condition['value'])

            elif condition['type'] == 'tag':
                response = self.shopware_service.get_tags()
                tags = {t['id']: t['name'] for t in response}
                return tags.get(condition['value'], condition['value'])

            return condition['value']

    def get_discount(self, discount_id: int) -> Dict[str, Any]:
        """Get a specific discount"""
        discount = self.db.query(Discount).filter(Discount.id == discount_id).first()
        if not discount:
            raise Exception('Discount not found')

        return {
            'id': discount.id,
            'name': discount.name,
            'percentage': discount.percentage,
            'conditions': discount.conditions,
            'affected_products': discount.affected_products,
            'created_at': discount.created_at.isoformat()
        }

    def delete_discount(self, discount_id: int):
        """Delete a discount and restore original prices"""
        try:
            print(f"Attempting to delete discount {discount_id}")  # Debug log

            # Find the discount
            discount = self.db.query(Discount).filter(Discount.id == discount_id).first()
            if not discount:
                print(f"Discount {discount_id} not found")  # Debug log
                raise Exception('Discount not found')

            print(f"Found discount: {discount.name}")  # Debug log

            try:
                # Get matching products to restore prices
                matching_products = self.shopware_service.get_matching_products(discount.conditions)
                print(f"Found {len(matching_products)} products to restore")  # Debug log

                # Collect product IDs
                product_ids = [p['id'] for p in matching_products if p.get('id')]

                if product_ids:
                    # Restore all prices in one go
                    restore_results = self.shopware_service.restore_product_prices(product_ids)

                    # Log results
                    success_count = len([r for r in restore_results if r['status'] == 'success'])
                    error_count = len([r for r in restore_results if r['status'] == 'error'])
                    print(f"Price restoration complete: {success_count} successful, {error_count} failed")
                else:
                    print("No products found to restore prices for")

            except Exception as restore_error:
                print(f"Error restoring prices: {str(restore_error)}")
                # Continue with deletion even if price restoration fails
                pass

            # Delete from database
            print("Deleting discount from database")  # Debug log
            self.db.delete(discount)
            self.db.commit()
            print("Discount deleted successfully")  # Debug log

        except Exception as e:
            print(f"Error in delete_discount: {str(e)}")  # Debug log
            import traceback
            print(f"Traceback: {traceback.format_exc()}")  # Full error traceback
            self.db.rollback()
            raise

        finally:
            self.db.close()

    def __del__(self):
        """Close database session"""
        self.db.close()
