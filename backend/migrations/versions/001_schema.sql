-- Frozen bootstrap schema. Subsequent changes belong to forward migrations.

CREATE TABLE audit_events (
	id UUID NOT NULL, 
	actor VARCHAR(64), 
	action VARCHAR(100) NOT NULL, 
	target VARCHAR(100), 
	detail JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE campaign_revisions (
	id UUID NOT NULL, 
	department VARCHAR(10) NOT NULL, 
	revision INTEGER NOT NULL, 
	content JSONB NOT NULL, 
	published BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (department, revision)
);

CREATE UNIQUE INDEX one_live_campaign ON campaign_revisions (department) WHERE published IS true;

CREATE TABLE carts (
	owner_id VARCHAR(64) NOT NULL, 
	version INTEGER NOT NULL, 
	PRIMARY KEY (owner_id)
);

CREATE TABLE orders (
	id UUID NOT NULL, 
	number BIGINT NOT NULL, 
	owner_id VARCHAR(64) NOT NULL, 
	request_key VARCHAR(100) NOT NULL, 
	request_hash VARCHAR(64) NOT NULL, 
	cart_version INTEGER NOT NULL, 
	address JSONB NOT NULL, 
	subtotal INTEGER NOT NULL, 
	shipping INTEGER NOT NULL, 
	total INTEGER NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	fulfilment VARCHAR(30) NOT NULL, 
	delivered_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	provider_order_id VARCHAR(100), 
	payment_id VARCHAR(100), 
	payment_mode VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (owner_id, request_key), 
	UNIQUE (number), 
	UNIQUE (provider_order_id), 
	UNIQUE (payment_id)
);

CREATE TABLE outbox_jobs (
	id UUID NOT NULL, 
	operation_key VARCHAR(200) NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	payload JSONB NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	attempts INTEGER NOT NULL, 
	due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	lease_until TIMESTAMP WITH TIME ZONE, 
	last_error VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (operation_key)
);

CREATE TABLE products (
	id UUID NOT NULL, 
	slug VARCHAR(150) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	department VARCHAR(10) NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	description TEXT NOT NULL, 
	material VARCHAR(200) NOT NULL, 
	care TEXT NOT NULL, 
	details JSONB NOT NULL, 
	media JSONB NOT NULL, 
	relations JSONB NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (department in ('women','home')), 
	CHECK (status in ('draft','published','archived')), 
	UNIQUE (slug)
);

CREATE TABLE profiles (
	id UUID NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	name VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE rate_limits (
	key VARCHAR(160) NOT NULL, 
	"window" BIGINT NOT NULL, 
	count INTEGER NOT NULL, 
	PRIMARY KEY (key)
);

CREATE TABLE shop_settings (
	key VARCHAR(50) NOT NULL, 
	value JSONB NOT NULL, 
	PRIMARY KEY (key)
);

CREATE TABLE support_requests (
	id UUID NOT NULL, 
	owner_id VARCHAR(64) NOT NULL, 
	request_key VARCHAR(100) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (owner_id, request_key)
);

CREATE TABLE webhook_events (
	event_id VARCHAR(150) NOT NULL, 
	body_hash VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (event_id)
);

CREATE TABLE product_variants (
	id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	sku VARCHAR(80) NOT NULL, 
	colour VARCHAR(60) NOT NULL, 
	colour_hex VARCHAR(7) NOT NULL, 
	size VARCHAR(80) NOT NULL, 
	dimensions VARCHAR(100), 
	price_paise INTEGER NOT NULL, 
	compare_at_paise INTEGER, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (product_id, colour, size), 
	CHECK (price_paise > 0), 
	CHECK (compare_at_paise is null or compare_at_paise > price_paise), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	UNIQUE (sku)
);

CREATE TABLE refunds (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	request_key VARCHAR(100) NOT NULL, 
	amount INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	provider_id VARCHAR(100), 
	reason VARCHAR(300) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id, request_key), 
	CHECK (amount > 0), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	UNIQUE (provider_id)
);

CREATE TABLE return_requests (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	request_key VARCHAR(100) NOT NULL, 
	items JSONB NOT NULL, 
	reason VARCHAR(500) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	sellable BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id, request_key), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);

CREATE TABLE saved_items (
	owner_id VARCHAR(64) NOT NULL, 
	product_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (owner_id, product_id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE TABLE sessions (
	token_hash VARCHAR(64) NOT NULL, 
	owner_id VARCHAR(64) NOT NULL, 
	user_id UUID, 
	assurance VARCHAR(10), 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
);

CREATE TABLE shipments (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	tracking VARCHAR(300) NOT NULL, 
	items JSONB NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
);

CREATE TABLE staff_memberships (
	user_id UUID NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
);

CREATE TABLE cart_items (
	owner_id VARCHAR(64) NOT NULL, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (owner_id, variant_id), 
	CHECK (quantity between 1 and 10), 
	FOREIGN KEY(owner_id) REFERENCES carts (owner_id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
);

CREATE TABLE inventory (
	variant_id UUID NOT NULL, 
	on_hand INTEGER NOT NULL, 
	reserved INTEGER NOT NULL, 
	PRIMARY KEY (variant_id), 
	CHECK (on_hand >= reserved and reserved >= 0), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
);

CREATE TABLE order_items (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	snapshot JSONB NOT NULL, 
	quantity INTEGER NOT NULL, 
	price_paise INTEGER NOT NULL, 
	reservation VARCHAR(20) NOT NULL, 
	shipped INTEGER NOT NULL, 
	returned INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0 and shipped >= 0 and shipped <= quantity and returned >= 0 and returned <= shipped), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
);

CREATE TABLE stock_movements (
	id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	operation_key VARCHAR(200) NOT NULL, 
	on_hand_delta INTEGER NOT NULL, 
	reserved_delta INTEGER NOT NULL, 
	reason VARCHAR(300) NOT NULL, 
	actor VARCHAR(64), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	UNIQUE (operation_key)
);
