import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Business, AIEmployee, AITask
from services import (
    EnhancedBusinessIntelligenceService,
    LLCBuilderService,
    AIWorkforceService
)
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database setup
engine = create_engine('sqlite:///llc_formation.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

async def main():
    # Initialize services
    llc_builder = LLCBuilderService(session)
    ai_workforce = AIWorkforceService(session)
    bi_service = EnhancedBusinessIntelligenceService(session)

    # Create a new LLC
    business = await llc_builder.create_llc(
        name="AI Innovations LLC",
        industry="Technology",
        state="Delaware",
        is_nonprofit=False,
        tax_classification="LLC",
        mission_statement="Leveraging AI to transform businesses"
    )

    # Hire AI employees
    ai_employees = []
    roles = [
        ("Technical Lead", "Engineering"),
        ("Marketing Specialist", "Marketing"),
        ("Data Analyst", "Analytics")
    ]

    for role, department in roles:
        employee = await ai_workforce.hire_employee(
            business_id=business.id,
            role=role,
            department=department
        )
        ai_employees.append(employee)

    # Assign tasks to employees
    tasks = [
        ("Develop AI Strategy", "Create a comprehensive AI strategy for the company", "high"),
        ("Market Analysis", "Conduct market research for AI products", "medium"),
        ("Performance Analytics", "Analyze company performance metrics", "medium")
    ]

    for i, (title, description, priority) in enumerate(tasks):
        await ai_workforce.assign_task(
            business_id=business.id,
            employee_id=ai_employees[i].id,
            title=title,
            description=description,
            priority=1 if priority == "high" else 2
        )

    # Generate business insights
    insights = await bi_service.analyze_business(business.id)
    print("\nBusiness Insights:")
    print(insights)

    # Generate department performance report
    dept_performance = await ai_workforce.analyze_department_performance(business.id)
    print("\nDepartment Performance:")
    print(dept_performance)

if __name__ == "__main__":
    asyncio.run(main())
