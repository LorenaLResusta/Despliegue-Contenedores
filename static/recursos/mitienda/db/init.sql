-- Esquema y datos iniciales de MiTienda (PostgreSQL).
-- La imagen oficial de postgres ejecuta los ficheros de /docker-entrypoint-initdb.d/
-- SOLO la primera vez, cuando el directorio de datos está vacío.
CREATE TABLE IF NOT EXISTS producto (
    id         SERIAL PRIMARY KEY,
    nombre     VARCHAR(80)   NOT NULL UNIQUE,
    categoria  VARCHAR(60)   NOT NULL,
    precio     NUMERIC(8,2)  NOT NULL CHECK (precio >= 0),
    stock      SMALLINT      NOT NULL CHECK (stock >= 0)
);

INSERT INTO producto (nombre, categoria, precio, stock) VALUES
    ('Camiseta básica',        'Ropa',        9.95,  40),
    ('Sudadera con capucha',   'Ropa',       24.95,  18),
    ('Zapatillas deportivas',  'Calzado',    49.90,  12),
    ('Gorra de algodón',       'Complementos', 7.50, 25),
    ('Mochila urbana',         'Complementos',29.00,  9),
    ('Botella térmica 500 ml', 'Hogar',      14.90,  30),
    ('Taza de cerámica',       'Hogar',       6.95,  50),
    ('Auriculares inalámbricos','Tecnología', 19.99,  7)
ON CONFLICT (nombre) DO NOTHING;
