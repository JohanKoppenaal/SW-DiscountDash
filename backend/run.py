from flask import Flask, request, jsonify
from flask_cors import CORS
from database import save_credentials, get_credentials, get_discounts, save_discount, delete_discount, get_db  # get_db toegevoegd
import json  # Voeg ook json import toe voor json.loads
from app.services.shopware import ShopwareService

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080", "supports_credentials": True}})
shopware_service = ShopwareService()

@app.route('/api/save_credentials', methods=['POST'])
def api_save_credentials():
    print("Received save_credentials request")  # Debug log
    print("Headers:", dict(request.headers))    # Debug log

    try:
        data = request.get_json()
        print("Data:", data)         # Debug log

        shop_url = data.get("shop_url")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")

        if not (shop_url and client_id and client_secret):
            print("Missing required fields")  # Debug log
            return jsonify({"error": "Missing data"}), 400

        save_credentials(shop_url, client_id, client_secret)
        print("Credentials saved successfully")  # Debug log
        return jsonify({"message": "Credentials saved successfully"}), 200
    except Exception as e:
        print(f"Error saving credentials: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_credentials', methods=['GET'])
def api_get_credentials():
    print("Received GET request for credentials")  # Debug log
    try:
        credentials = get_credentials()
        if credentials:
            return jsonify(credentials), 200
        print("No credentials found")  # Debug log
        return jsonify({"error": "No credentials found"}), 404
    except Exception as e:
        print(f"Error getting credentials: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_connection', methods=['GET'])
def test_connection():
    try:
        credentials = get_credentials()
        if not credentials:
            return jsonify({"status": "error", "message": "No credentials found"}), 404

        # Hier kunnen we een test request naar Shopware doen
        # Voor nu returnen we success als we credentials hebben
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error testing connection: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/discounts', methods=['GET'])
def get_discounts_route():  # Gewijzigd van get_discounts() naar get_discounts_route()
    try:
        discounts = get_discounts()  # Deze komt uit database.py
        return jsonify({"status": "success", "data": discounts})
    except Exception as e:
        print(f"Error getting discounts: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/discounts', methods=['POST'])
def create_discount():
    try:
        print("Received discount creation request")  # Debug log
        data = request.json
        print("Request data:", data)  # Debug log

        if not all(key in data for key in ['name', 'percentage', 'conditions']):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400

        # Eerst de korting opslaan in onze database
        discount_id = save_discount(
            name=data['name'],
            percentage=float(data['percentage']),
            conditions=data['conditions']
        )

        # Dan de korting toepassen in Shopware
        print("Applying discount to Shopware products...")  # Debug log
        shopware_result = shopware_service.create_discount(
            name=data['name'],
            percentage=float(data['percentage']),
            conditions=data['conditions']
        )

        return jsonify({
            "status": "success",
            "message": "Discount created and applied successfully",
            "id": discount_id,
            "affected_products": shopware_result['affected_products']
        })
    except Exception as e:
        print(f"Error creating discount: {str(e)}")  # Debug log
        return jsonify({
            "status": "error",
            "message": f"Error creating discount: {str(e)}"
        }), 500

@app.route('/api/discounts/<int:discount_id>', methods=['DELETE'])
def delete_discount_route(discount_id):
    try:
        print(f"Deleting discount {discount_id}")  # Debug log

        # Eerst de korting ophalen
        with get_db() as db:
            discount = db.execute("SELECT * FROM discounts WHERE id = ?", (discount_id,)).fetchone()
            print(f"Found discount: {discount}")  # Debug log

            if not discount:
                return jsonify({"status": "error", "message": "Discount not found"}), 404

            conditions = json.loads(discount['conditions'])
            print(f"Parsed conditions: {conditions}")  # Debug log

        # Matchende producten vinden en prijzen resetten
        print("Finding matching products...")  # Debug log
        matching_products = shopware_service.get_matching_products(conditions)
        print(f"Found {len(matching_products)} matching products")  # Debug log

        product_ids = [p['id'] for p in matching_products]

        # Prijzen resetten
        print("Resetting prices...")  # Debug log
        if product_ids:
            shopware_service.restore_product_prices(product_ids)

        # Dan de korting verwijderen
        success = delete_discount(discount_id)
        if success:
            return jsonify({
                "status": "success",
                "message": "Discount deleted and prices restored successfully"
            })

        return jsonify({
            "status": "error",
            "message": "Could not delete discount"
        }), 500

    except Exception as e:
        print(f"Error deleting discount: {str(e)}")  # Debug log
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/product-manufacturer', methods=['GET'])
def get_manufacturers_route():
    try:
        manufacturers = shopware_service.get_manufacturers()
        return jsonify({"status": "success", "data": manufacturers})
    except Exception as e:
        print(f"Error getting manufacturers: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/category', methods=['GET'])
def get_categories_route():
    try:
        categories = shopware_service.get_categories()
        return jsonify({"status": "success", "data": categories})
    except Exception as e:
        print(f"Error getting categories: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tag', methods=['GET'])
def get_tags_route():
    try:
        tags = shopware_service.get_tags()
        return jsonify({"status": "success", "data": tags})
    except Exception as e:
        print(f"Error getting tags: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/preview-matching-products', methods=['POST'])
def preview_matching_products():
    try:
        conditions = request.json.get('conditions', [])
        print("Received conditions for preview:", conditions)  # Debug log

        matching_products = shopware_service.get_matching_products(conditions)

        preview_data = {
            "status": "success",
            "count": len(matching_products),
            "total_value": sum(p['price'][0]['gross'] for p in matching_products if p.get('price')),
            "sample": [  # Eerste 5 producten als voorbeeld
                {
                    "id": p['id'],
                    "name": p['name'],
                    "price": p['price'][0]['gross'] if p.get('price') else 0,
                    "listPrice": p['price'][0].get('listPrice', {}).get('gross') if p.get('price') and p['price'][0].get('listPrice') else None,
                    "number": p.get('productNumber', '')
                }
                for p in matching_products[:5]
            ]
        }

        return jsonify(preview_data)

    except Exception as e:
        print(f"Error in preview matching products: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Flask server...")  # Debug log
    app.run(debug=True)