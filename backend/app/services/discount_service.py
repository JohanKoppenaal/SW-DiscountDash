from typing import List, Dict, Any
from sqlalchemy.orm import Session, scoped_session
from ..models.discount import Discount, Session as DBSession
from .shopware import ShopwareService
from datetime import datetime

class DiscountService:
    def __init__(self):
        self.shopware_service = ShopwareService()
        self.db = DBSession()

    def get_discounts(self) -> List[Dict[str, Any]]:
            """Get all discounts with resolved names"""
            try:
                print("Fetching discounts from database...")  # Debug log
                discounts = self.db.query(Discount).order_by(Discount.created_at.desc()).all()
                print(f"Found {len(discounts)} discounts")  # Debug log

                result = []
                for d in discounts:
                    try:
                        formatted_conditions = []
                        for group in d.conditions:
                            formatted_group = {
                                'operator': group.get('operator', 'AND'),
                                'conditions': []
                            }

                            for condition in group.get('conditions', []):
                                name = self._get_name_for_condition(condition)
                                formatted_condition = {
                                    'type': condition.get('type', ''),
                                    'operator': condition.get('operator', ''),
                                    'value': condition.get('value', ''),
                                    'name': name
                                }
                                formatted_group['conditions'].append(formatted_condition)

                            formatted_conditions.append(formatted_group)

                        discount_dict = {
                            'id': d.id,
                            'name': d.name,
                            'percentage': float(d.percentage) if d.percentage else 0,
                            'conditions': formatted_conditions,
                            'affected_products': d.affected_products or 0,
                            'created_at': d.created_at.isoformat() if d.created_at else datetime.now().isoformat()
                        }
                        result.append(discount_dict)
                    except Exception as format_error:
                        print(f"Error formatting discount {d.id}: {str(format_error)}")
                        continue

                return result

            except Exception as e:
                print(f"Error in get_discounts: {str(e)}")
                raise

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
            condition_type = condition.get('type')
            condition_value = condition.get('value')

            print(f"Getting name for condition: type={condition_type}, value={condition_value}")  # Debug log

            if not condition_type or not condition_value:
                return 'Onbekend'

            if condition_type == 'manufacturer':
                print("Fetching manufacturers...")  # Debug log
                response = self.shopware_service.get_manufacturers()
                print(f"Found {len(response)} manufacturers")  # Debug log
                for manufacturer in response:
                    if manufacturer.get('id') == condition_value:
                        name = manufacturer.get('name', condition_value)
                        print(f"Found manufacturer name: {name}")  # Debug log
                        return name

            elif condition_type == 'category':
                print("Fetching categories...")  # Debug log
                response = self.shopware_service.get_categories()
                print(f"Found {len(response)} categories")  # Debug log
                for category in response:
                    if category.get('id') == condition_value:
                        name = category.get('name', condition_value)
                        print(f"Found category name: {name}")  # Debug log
                        return name

            elif condition_type == 'tag':
                print("Fetching tags...")  # Debug log
                response = self.shopware_service.get_tags()
                print(f"Found {len(response)} tags")  # Debug log
                for tag in response:
                    if tag.get('id') == condition_value:
                        name = tag.get('name', condition_value)
                        print(f"Found tag name: {name}")  # Debug log
                        return name

            print(f"No name found, returning value: {condition_value}")  # Debug log
            return str(condition_value)

        except Exception as e:
            print(f"Error getting name for condition: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")  # Full error trace
            return str(condition_value)


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
