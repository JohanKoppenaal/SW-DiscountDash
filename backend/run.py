from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 5000 is default, we kunnen ook 3000 of 8080 gebruiken