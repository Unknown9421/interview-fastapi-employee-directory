"""
Seed data script for initializing the database with sample data.
Run this script after migrations to populate the database.
"""
import asyncio
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.organization import Organization, OrganizationConfig
from app.models.employee import Employee, EmployeeStatus

# Sample data
ORGANIZATIONS = [
    {
        "name": "TechCorp International",
        "description": "Global technology solutions provider",
        "visible_columns": [
            "id", "avatar_url", "first_name", "last_name", "email", "phone",
            "status", "location", "company", "department", "position"
        ]
    },
    {
        "name": "HealthFirst Medical",
        "description": "Healthcare services organization",
        "visible_columns": [
            "id", "avatar_url", "first_name", "last_name", "email",
            "status", "department", "position"
        ]  # No phone, location, company
    },
    {
        "name": "EduLearn Academy",
        "description": "Educational institution",
        "visible_columns": [
            "id", "first_name", "last_name",
            "status", "department", "position"
        ]  # Minimal columns, no avatar
    },
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]

LOCATIONS = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "Seattle, WA", "Denver, CO", "Boston, MA", "Detroit, MI", "Portland, OR",
]

COMPANIES = [
    "Main Branch", "East Division", "West Division", "North Region", "South Region",
    "Corporate HQ", "Research Center", "Innovation Lab", "Support Center", "Sales Office",
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Human Resources", "Finance",
    "Operations", "Customer Service", "Research & Development", "Legal", "IT Support",
]

POSITIONS = [
    "Software Engineer", "Senior Developer", "Product Manager", "Marketing Specialist",
    "Sales Representative", "HR Coordinator", "Financial Analyst", "Operations Manager",
    "Customer Support Agent", "Research Scientist", "Legal Counsel", "System Administrator",
    "Data Analyst", "Project Manager", "Business Analyst", "Quality Assurance Engineer",
]

STATUSES = [EmployeeStatus.ACTIVE, EmployeeStatus.NOT_STARTED, EmployeeStatus.TERMINATED]


def generate_email(first_name: str, last_name: str, org_name: str) -> str:
    """Generate email address from name and organization."""
    domain = org_name.lower().replace(" ", "").replace(".", "")[:10]
    return f"{first_name.lower()}.{last_name.lower()}@{domain}.com"


async def seed_database():
    """Seed the database with sample organizations and employees."""
    async with AsyncSessionLocal() as session:
        # Check if data already exists
        result = await session.execute(select(Organization).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        # Create organizations with configs
        for org_data in ORGANIZATIONS:
            # Create organization
            org = Organization(
                name=org_data["name"],
                description=org_data["description"],
                is_active=True
            )
            session.add(org)
            await session.flush()  # Get the org ID

            # Create config
            config = OrganizationConfig(
                organization_id=org.id,
                visible_columns=org_data["visible_columns"]
            )
            session.add(config)

            # Create employees for this organization
            num_employees = random.randint(50, 150)
            for _ in range(num_employees):
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)

                # Generate avatar URL (using UI Avatars service as placeholder)
                avatar_url = f"https://ui-avatars.com/api/?name={first_name}+{last_name}&background=random"

                employee = Employee(
                    organization_id=org.id,
                    avatar_url=avatar_url,
                    first_name=first_name,
                    last_name=last_name,
                    email=generate_email(first_name, last_name, org_data["name"]),
                    phone=f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    status=random.choices(
                        STATUSES,
                        weights=[0.7, 0.2, 0.1]  # 70% Active, 20% Not started, 10% Terminated
                    )[0],
                    location=random.choice(LOCATIONS),
                    company=random.choice(COMPANIES),
                    department=random.choice(DEPARTMENTS),
                    position=random.choice(POSITIONS),
                    created_by="system",
                )
                session.add(employee)

            print(f"Created organization '{org_data['name']}' with {num_employees} employees")

        await session.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
