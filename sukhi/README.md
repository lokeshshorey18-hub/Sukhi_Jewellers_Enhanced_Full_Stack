
# Jewellery Shop — Full-Stack Starter

A self-contained Flask + SQLite jewellery-store starter with a real admin panel.

## Included

- Public responsive jewellery storefront
- Gold / Silver / Diamond categories
- Daily 24K gold rate
- Automatic 22K / 18K / 14K calculation:
  `carat rate = 24K rate × carat / 24`
- Gold metal value:
  `weight × carat rate`
- Product weight, purity, making charges, stone charges and other charges
- Internal cost price stored in database and not displayed publicly
- MRP, selling price and automatic discount display
- Image upload
- Product archive
- Admin login with hashed password
- SQLite database
- Basic order table and checkout endpoint placeholder
- API endpoint for current metal rates

## Run locally

1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Create a virtual environment:
   Windows:
   `py -m venv .venv`
   `.venv\Scripts\activate`
   macOS/Linux:
   `python3 -m venv .venv`
   `source .venv/bin/activate`
4. Install:
   `pip install -r requirements.txt`
5. Optional: set environment variables:
   `ADMIN_USER=yourusername`
   `ADMIN_PASSWORD=yourstrongpassword`
   `SECRET_KEY=long-random-secret`
6. Start:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`
8. Admin:
   `http://127.0.0.1:5000/admin`

Default demo credentials if environment variables were not set:
Username: `admin`
Password: `ChangeMe123!`

CHANGE THE DEFAULT PASSWORD BEFORE ANY REAL DEPLOYMENT.

## Important production work still required

This is a strong development starter, not a production payment system.

Before launch we should add:
- PostgreSQL/MySQL instead of SQLite for production
- Production WSGI server (Gunicorn/waitress depending on host)
- HTTPS/TLS at the hosting/reverse-proxy layer
- CSRF protection
- Secure cookie configuration
- Rate limiting / login lockout
- Admin password change and 2FA
- Image resizing/optimization
- Product edit screen
- Inventory/stock management
- Customer accounts if required
- GST/tax configuration
- Shipping integration
- Razorpay server-side order creation, signature verification and webhooks
- Real cart persistence
- Order status workflow
- Email/WhatsApp notifications
- Backups and monitoring
- Privacy, refund, shipping and terms pages
- Server-side authoritative price calculation at checkout

## Pricing model

For Gold:
24K daily rate is entered by admin.
22K rate = 24K rate × 22 / 24.
18K rate = 24K rate × 18 / 24.
14K rate = 24K rate × 14 / 24.
Gold metal value = selected carat rate × weight.

Completed orders should store a price snapshot so historical orders never change when tomorrow's gold rate changes.

## Suggested next milestone

Convert this starter into a production-ready deployment using:
- WordPress/WooCommerce OR
- Flask/PostgreSQL (this architecture)

For maximum control over the pricing engine, a custom Flask/PostgreSQL application is a good long-term choice. For the least maintenance, WordPress/WooCommerce remains simpler.

## Enhanced navigation and homepage
- Multi-level dropdown navigation with Shop By Category, New Arrivals, Best Seller, Info and Our Policy.
- Admin-managed marquee/news, social links and homepage hero images.
- Category pages, New Arrivals, Best Sellers and Shop by Price pages.
- Admin Navigation Manager for adding tabs, categories and sub-categories.
- Enhanced responsive homepage with category strip and product carousel-style layout.

Next production milestones: editable homepage sections, multiple product images with zoom, real cart/wishlist/customer login, Razorpay payment verification, product editing/inventory, and production security hardening.
