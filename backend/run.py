from flask import Flask, request, jsonify
from flask_cors import CORS
from database import save_credentials, get_credentials, get_discounts, save_discount, delete_discount
from shopware import ShopwareService

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

        discount_id = save_discount(
            name=data['name'],
            percentage=float(data['percentage']),
            conditions=data['conditions']
        )

        return jsonify({
            "status": "success",
            "message": "Discount created successfully",
            "id": discount_id
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
        success = delete_discount(discount_id)
        if success:
            return jsonify({"status": "success", "message": "Discount deleted successfully"})
        return jsonify({"status": "error", "message": "Discount not found"}), 404
    except Exception as e:
        print(f"Error deleting discount: {str(e)}")
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
        # Voor nu, een dummy aantal teruggeven
        return jsonify({
            "status": "success",
            "count": 42,  # Dummy aantal
            "sample": []  # Later kunnen we hier voorbeeldproducten toevoegen
        })
    except Exception as e:
        print(f"Error preview matching products: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")  # Debug log
    app.run(debug=True)