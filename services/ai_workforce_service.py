import openai
from sqlalchemy.orm import Session
from models import AIEmployee, AITask, Business
from typing import Dict, List, Any
from datetime import datetime
import json
import os
from openai import AsyncOpenAI

class AIWorkforceService:
    def __init__(self, session: Session):
        self.session = session
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def hire_employee(self, business_id: int, role: str, department: str) -> AIEmployee:
        """Hire a new AI employee with specified role and department."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError(f"Business with ID {business_id} not found")

        # Generate employee details using OpenAI
        prompt = f"""
        Create a profile for an AI employee with the following:
        Role: {role}
        Department: {department}
        Business: {business.name} ({business.industry})

        Include:
        1. A professional name
        2. Key skills and capabilities
        3. Performance metrics to track
        """

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an HR expert specializing in AI workforce."},
                {"role": "user", "content": prompt}
            ]
        )

        profile = json.loads(response.choices[0].message.content)

        employee = AIEmployee(
            name=profile["name"],
            role=role,
            department=department,
            skills=profile["skills"],
            performance_metrics={"metrics": profile["performance_metrics"]},
            business_id=business_id
        )

        self.session.add(employee)
        self.session.commit()
        return employee

    async def assign_task(self, business_id: int, employee_id: int, title: str, description: str, priority: int) -> AITask:
        """Assign a task to an AI employee."""
        employee = self.session.query(AIEmployee).get(employee_id)
        if not employee or employee.business_id != business_id:
            raise ValueError("Invalid employee ID or business ID")

        task = AITask(
            title=title,
            description=description,
            status="pending",
            priority=priority,
            business_id=business_id,
            employee_id=employee_id,
            completion_rate=0.0,
            metrics={}
        )

        self.session.add(task)
        self.session.commit()
        return task

    async def analyze_department_performance(self, business_id: int) -> Dict[str, Any]:
        """Analyze performance metrics for all departments."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError(f"Business with ID {business_id} not found")

        departments = {}
        employees = self.session.query(AIEmployee).filter_by(business_id=business_id).all()

        for employee in employees:
            if employee.department not in departments:
                departments[employee.department] = {
                    "employee_count": 0,
                    "completed_tasks": 0,
                    "total_tasks": 0,
                    "average_completion_rate": 0.0
                }

            dept = departments[employee.department]
            dept["employee_count"] += 1

            tasks = self.session.query(AITask).filter_by(employee_id=employee.id).all()
            dept["total_tasks"] += len(tasks)
            dept["completed_tasks"] += len([t for t in tasks if t.status == "completed"])
            completion_rates = [t.completion_rate for t in tasks if t.completion_rate is not None]
            if completion_rates:
                dept["average_completion_rate"] = sum(completion_rates) / len(completion_rates)

        return departments
