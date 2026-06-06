"""Seed the database with demo data.

Run with:  python -m app.seed
Safe to run multiple times — it skips seeding if data already exists.
"""
import asyncio
import datetime as dt
from decimal import Decimal

from sqlalchemy import func, select

from .database import SessionLocal, init_models
from .models import (
    Activity,
    Contact,
    Customer,
    Lead,
    Order,
    OrderItem,
    Product,
    User,
)
from .security import hash_password


async def seed() -> None:
    await init_models()
    async with SessionLocal() as db:
        existing = await db.scalar(select(func.count(User.id)))
        if existing:
            print("Database already seeded — skipping.")
            return

        admin = User(
            email="admin@clothcrm.local",
            full_name="Avery Stone",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        rep = User(
            email="sales@clothcrm.local",
            full_name="Jordan Pike",
            hashed_password=hash_password("sales123"),
            role="sales",
        )
        db.add_all([admin, rep])
        await db.flush()

        products = [
            Product(sku="TS-CL-001", name="Classic Cotton Tee", category="T-Shirts", size="M", color="White", unit_price=Decimal("6.50"), stock_qty=1200),
            Product(sku="TS-CL-002", name="Classic Cotton Tee", category="T-Shirts", size="L", color="Black", unit_price=Decimal("6.50"), stock_qty=18),
            Product(sku="SH-OX-010", name="Oxford Shirt", category="Shirts", size="M", color="Blue", unit_price=Decimal("14.00"), stock_qty=340),
            Product(sku="TR-CH-020", name="Chino Trousers", category="Trousers", size="32", color="Khaki", unit_price=Decimal("19.90"), stock_qty=210),
            Product(sku="JK-DN-030", name="Denim Jacket", category="Jackets", size="L", color="Indigo", unit_price=Decimal("34.00"), stock_qty=12),
            Product(sku="DR-SM-040", name="Summer Dress", category="Dresses", size="S", color="Floral", unit_price=Decimal("22.50"), stock_qty=95),
            Product(sku="KN-WL-050", name="Wool Jumper", category="Knitwear", size="M", color="Grey", unit_price=Decimal("27.00"), stock_qty=140),
            Product(sku="AC-CP-060", name="Baseball Cap", category="Accessories", size="One", color="Navy", unit_price=Decimal("5.25"), stock_qty=500),
        ]
        db.add_all(products)
        await db.flush()

        customers = [
            Customer(company_name="Northwind Retail Group", customer_type="Retailer", email="buying@northwind.example", phone="+44 20 7946 0102", city="London", country="United Kingdom", status="Active", credit_limit=Decimal("50000"), owner_id=admin.id),
            Customer(company_name="Astra Distribution BV", customer_type="Distributor", email="orders@astra.example", phone="+31 20 555 0143", city="Amsterdam", country="Netherlands", status="Active", credit_limit=Decimal("120000"), owner_id=rep.id),
            Customer(company_name="Bella Boutique", customer_type="Boutique", email="hello@bellaboutique.example", phone="+39 02 555 0177", city="Milan", country="Italy", status="Prospect", credit_limit=Decimal("8000"), owner_id=rep.id),
            Customer(company_name="UrbanThreads Online", customer_type="Online Store", email="procurement@urbanthreads.example", phone="+1 415 555 0190", city="San Francisco", country="United States", status="Active", credit_limit=Decimal("75000"), owner_id=admin.id),
            Customer(company_name="Meridian Wholesale Co", customer_type="Wholesaler", email="sales@meridian.example", phone="+61 2 5550 0188", city="Sydney", country="Australia", status="Inactive", credit_limit=Decimal("30000"), owner_id=admin.id),
        ]
        db.add_all(customers)
        await db.flush()

        db.add_all([
            Contact(customer_id=customers[0].id, first_name="Sam", last_name="Carter", title="Head of Buying", email="sam.carter@northwind.example", phone="+44 20 7946 0110", is_primary=True),
            Contact(customer_id=customers[1].id, first_name="Lotte", last_name="de Vries", title="Procurement Manager", email="lotte@astra.example", is_primary=True),
            Contact(customer_id=customers[3].id, first_name="Riley", last_name="Nguyen", title="Category Lead", email="riley@urbanthreads.example", is_primary=True),
        ])

        leads = [
            Lead(title="AW collection bulk order", customer_id=customers[0].id, stage="Proposal", value=Decimal("42000"), probability=60, source="Trade show", expected_close_date=dt.date.today() + dt.timedelta(days=21), owner_id=admin.id),
            Lead(title="Annual distribution contract", customer_id=customers[1].id, stage="Negotiation", value=Decimal("180000"), probability=75, source="Referral", expected_close_date=dt.date.today() + dt.timedelta(days=40), owner_id=rep.id),
            Lead(title="Boutique trial range", customer_id=customers[2].id, stage="Qualified", value=Decimal("9500"), probability=40, source="Inbound", owner_id=rep.id),
            Lead(title="Online exclusive line", customer_id=customers[3].id, stage="Won", value=Decimal("61000"), probability=100, source="Account expansion", owner_id=admin.id),
            Lead(title="Clearance stock enquiry", customer_id=customers[4].id, stage="Lost", value=Decimal("15000"), probability=0, source="Cold outreach", owner_id=admin.id),
            Lead(title="New season teaser", customer_id=customers[0].id, stage="New", value=Decimal("23000"), probability=15, source="Website", owner_id=rep.id),
        ]
        db.add_all(leads)
        await db.flush()

        order1 = Order(order_number="SO-2026-0001", customer_id=customers[0].id, status="Confirmed", order_date=dt.date.today() - dt.timedelta(days=5))
        order2 = Order(order_number="SO-2026-0002", customer_id=customers[3].id, status="Shipped", order_date=dt.date.today() - dt.timedelta(days=2))
        db.add_all([order1, order2])
        await db.flush()

        items = [
            OrderItem(order_id=order1.id, product_id=products[0].id, quantity=400, unit_price=products[0].unit_price),
            OrderItem(order_id=order1.id, product_id=products[2].id, quantity=120, unit_price=products[2].unit_price),
            OrderItem(order_id=order2.id, product_id=products[5].id, quantity=80, unit_price=products[5].unit_price),
            OrderItem(order_id=order2.id, product_id=products[6].id, quantity=60, unit_price=products[6].unit_price),
        ]
        db.add_all(items)
        await db.flush()
        for order in (order1, order2):
            await db.refresh(order, attribute_names=["items"])
            order.recalculate_total()

        db.add_all([
            Activity(type="Call", subject="Discuss AW pricing", customer_id=customers[0].id, due_date=dt.date.today() + dt.timedelta(days=2), owner_id=admin.id),
            Activity(type="Meeting", subject="Contract review with Astra", customer_id=customers[1].id, due_date=dt.date.today() + dt.timedelta(days=7), owner_id=rep.id),
            Activity(type="Email", subject="Send sample pack", customer_id=customers[2].id, completed=True, owner_id=rep.id),
            Activity(type="Task", subject="Prepare clearance quote", customer_id=customers[4].id, due_date=dt.date.today() - dt.timedelta(days=1), owner_id=admin.id),
        ])

        await db.commit()
        print("Seeded demo data.")
        print("  Admin login: admin@clothcrm.local / admin123")
        print("  Sales login: sales@clothcrm.local / sales123")


if __name__ == "__main__":
    asyncio.run(seed())
