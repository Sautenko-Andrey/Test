
CREATE TABLE IF NOT EXISTS cars (
    id  SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    price_usd INTEGER,
    odometer INTEGER,
    username TEXT,
    phone_number BIGINT,
    image_url TEXT,
    images_count INTEGER,
    car_number TEXT,
    car_vin TEXT,
    datetime_found TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
