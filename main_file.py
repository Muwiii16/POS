from thefuzz import process

products = {
    "pants": {
        "variants": {
            "small": {"price": 500, "stock": 10},
            "medium": {"price": 700, "stock": 20},
            "large": {"price": 900, "stock": 30}
        }
    },
    "notebooks": {
        "variants": {
            "80-leaves": {"price": 30, "stock": 100},
            "100-leaves": {"price": 50, "stock": 200}
        }
    }
}

cart = []

while True:
    print("\n ---Inventory---")
    for product, details in products.items():
        print(f'-{product.capitalize()}')

    user_input = input(
        "\nSearch product (or type 'checkout' to finish): ").strip().lower()
    if user_input == 'checkout':
        break

    match_result = process.extractOne(user_input, products.keys())
    if match_result and match_result[1] > 60:
        target_product = match_result[0]
        print(f'Showing options for {target_product.capitalize()}:')

        variants = products[target_product]["variants"]
        for key, value in variants.items():
            print(
                f'->{key} - Price: {value['price']}, Stock: {value["stock"]}')

        variant_choice = input("Please select a variant: ").strip().lower()
        if variant_choice in variants:
            selected = variants[variant_choice]

            if selected["stock"] > 0:
                selected["stock"] -= 1
                cart.append({
                    "name": target_product,
                    "variant": variant_choice,
                    "price": selected["price"]
                })
                print(
                    f"Added to cart! Current Total: ₱{sum(item['price'] for item in cart)}")
            else:
                print("Sorry, out of stock!")
        else:
            print("Invalid variant selected.")
    else:
        print("Product not found. Please try again.")

    print("\n--- Final Bill ---")
    grand_total = 0
    for item in cart:
        print(f'{item['name']}: ₱{item['price']}')
        grand_total += item['price']

    print(f'Grand Total: ₱{grand_total}')
    print("Thank you for shopping with us!")
