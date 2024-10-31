from flask import Blueprint, request, jsonify
from ..services.shopware import ShopwareService
from ..services.discount_service import DiscountService  # Nieuwe import

bp = Blueprint('api', __name__, url_prefix='/api')
shopware_service = ShopwareService()
discount_service = DiscountService()  # Service initialiseren

@bp.route('/credentials', methods=['GET', 'POST'])
def manage_credentials():
    if request.method == 'POST':
        data = request.json
        shopware_service.save_credentials(
            data['url'],
            data['client_id'],
            data['client_secret']
        )
        return jsonify({'status': 'success'})
    else:
        with get_db() as db:
            creds = db.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1").fetchone()
            if creds:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'url': creds['shop_url'],
                        'client_id': creds['client_id'],
                        'client_secret': creds['client_secret']
                    }
                })
            return jsonify({'status': 'error', 'message': 'No credentials found'}), 404

@bp.route('/connect', methods=['POST'])
def connect():
    data = request.json
    url = data.get('url')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')

    try:
        # Test connection with provided credentials
        success = shopware_service.test_connection(url, client_id, client_secret)
        if success:
            return jsonify({'status': 'success', 'message': 'Successfully connected to Shopware'})
        return jsonify({'status': 'error', 'message': 'Could not connect to Shopware'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/products/prices', methods=['GET'])
def get_prices():
    try:
        prices = shopware_service.get_product_prices()
        return jsonify({'status': 'success', 'data': prices})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/products/prices', methods=['PATCH'])
def update_prices():
    try:
        data = request.json
        updates = [data]  # Voor nu doen we één product
        results = shopware_service.update_product_prices(updates)
        return jsonify({'status': 'success', 'data': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/product-manufacturer', methods=['GET'])
def get_manufacturers():
    try:
        print("Getting manufacturers...")  # Debug log
        manufacturers = shopware_service.get_manufacturers()
        print(f"Found {len(manufacturers)} manufacturers")  # Debug log
        return jsonify({'status': 'success', 'data': manufacturers})
    except Exception as e:
        print(f"Error getting manufacturers: {str(e)}")  # Debug log
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/category', methods=['GET'])
def get_categories():
    try:
        print("API: Getting categories...")  # Debug log
        categories = shopware_service.get_categories()
        return jsonify({'status': 'success', 'data': categories})
    except Exception as e:
        print(f"API Error getting categories: {str(e)}")  # Debug log
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/tag', methods=['GET'])
def get_tags():
    try:
        print("API: Getting tags...")  # Debug log
        tags = shopware_service.get_tags()
        return jsonify({'status': 'success', 'data': tags})
    except Exception as e:
        print(f"API Error getting tags: {str(e)}")  # Debug log
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/preview-matching-products', methods=['POST'])
def preview_matching_products():
    try:
        conditions = request.json.get('conditions', [])
        matching_products = shopware_service.get_matching_products(conditions)
        return jsonify({
            'status': 'success',
            'count': len(matching_products),
            'sample': matching_products[:5]  # Eerste 5 producten als voorbeeld
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/discounts', methods=['POST'])
def create_discount():
    try:
        print("Creating discount - received data:", request.json)  # Debug log
        data = request.json

        # Validate required fields
        required_fields = ['name', 'percentage', 'conditions']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Create discount
        print("Creating discount with validated data")  # Debug log
        result = discount_service.create_discount(data)
        print("Discount created successfully:", result)  # Debug log

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        print(f"Error creating discount: {str(e)}")  # Debug log
        print(f"Error type: {type(e)}")  # Debug log
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Full error traceback
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/discounts', methods=['GET'])
def get_discounts():
    try:
        print("Getting discounts from database...")  # Debug log
        discounts = discount_service.get_discounts()
        print(f"Found {len(discounts)} discounts")  # Debug log
        return jsonify({'status': 'success', 'data': discounts})
    except Exception as e:
        print(f"Error getting discounts: {str(e)}")  # Debug log
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@bp.route('/discounts/<int:discount_id>', methods=['DELETE'])
def delete_discount(discount_id):
    try:
        print(f"API: Deleting discount {discount_id}")  # Debug log
        discount_service.delete_discount(discount_id)
        return jsonify({'status': 'success', 'message': 'Discount deleted successfully'})
    except Exception as e:
        print(f"API Error deleting discount: {str(e)}")  # Debug log
        import traceback
        print(f"API Error traceback: {traceback.format_exc()}")  # Full error traceback
        return jsonify({
            'status': 'error',
            'message': f'Could not delete discount: {str(e)}'
        }), 500