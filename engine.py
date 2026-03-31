# from thefuzz import process

# import core.models
# import core.inventory

# cart = []

# while True:
#     print("\n ---Inventory---")
#     unique_names = set(item.name for item in core.inventory.Store_Products)
#     for name in unique_names:
#         print(f'-> {name}')

#     user_input = input(
#         "\nSearch product (or type 'checkout' to finish): ").strip().lower()
#     if user_input == 'checkout':
#         break

#     product_names = [item.name for item in core.inventory.Store_Products]

#     match_result = process.extractOne(user_input, product_names)
#     if match_result and match_result[1] > 60:
#         target_product = match_result[0]
#         print(f'Showing options for {target_product.capitalize()}:')

#         variants = [
#             item for item in core.inventory.Store_Products if item.name == target_product]
#         for item in variants:
#             print(
#                 f'-> {item.variant} - Price: {item.price}, Stock: {item.stock}, Barcode: {item.barcode}')

#         variant_choice = input("Please select a variant: ").strip().lower()
#         if variant_choice in variants:
#             selected = variants[variant_choice]

#             if selected["stock"] > 0:
#                 selected["stock"] -= 1
#                 cart.append({
#                     "name": target_product,
#                     "variant": variant_choice,
#                     "price": selected["price"]
#                 })
#                 print(
#                     f"Added to cart! Current Total: ₱{sum(item['price'] for item in cart)}")
#             else:
#                 print("Sorry, out of stock!")
#         else:
#             print("Invalid variant selected.")
#     else:
#         print("Product not found. Please try again.")

#     print("\n--- Final Bill ---")
#     grand_total = 0
#     for item in cart:
#         print(f'{item['name']}: ₱{item['price']}')
#         grand_total += item['price']

#     print(f'Grand Total: ₱{grand_total}')
#     print("Thank you for shopping with us!")
