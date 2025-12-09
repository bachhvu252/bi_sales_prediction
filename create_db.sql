-- 1. Create Categories (e.g., Smartphone, Tablet, Accessory)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- 2. Create Brands (e.g., Apple, Samsung, Xiaomi)
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    origin_country VARCHAR(100)
);

-- 3. Create Staff/Users (Employees processing sales)
CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'Salesperson', -- Admin, Manager, Salesperson
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. Create Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone_number VARCHAR(20) UNIQUE NOT NULL, -- Critical for Mobile shops
    address TEXT,
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 5. Create Products
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL, -- e.g., "iPhone 15 Pro"
    sku VARCHAR(50) UNIQUE NOT NULL, -- Stock Keeping Unit
    brand_id INT REFERENCES brands(brand_id),
    category_id INT REFERENCES categories(category_id),
    
    -- Mobile Specific Specs
    color VARCHAR(50),
    storage_capacity_gb INT, -- e.g., 128, 256, 512
    ram_gb INT, -- e.g., 8, 12
    
    -- Financials
    cost_price DECIMAL(10, 2) NOT NULL, -- How much you bought it for
    selling_price DECIMAL(10, 2) NOT NULL, -- How much you sell it for
    
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 6. Create Orders (The Header)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    staff_id INT REFERENCES staff(staff_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Financials
    total_amount DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Status Tracking
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Completed, Cancelled, Returned
    notes TEXT
);

-- 7. Create Order Items (The specific phones in the box)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL, -- Price AT THE MOMENT of sale
    subtotal DECIMAL(10, 2) NOT NULL,
    
    -- Unique Identifier for Warranty
    imei_serial_number VARCHAR(100) -- Important: Track the specific phone sold
);

-- 8. Create Payments
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL -- Cash, Credit Card, Bank Transfer
);