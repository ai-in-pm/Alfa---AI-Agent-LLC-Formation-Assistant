from datetime import datetime, timedelta
from models import ComplianceItem, Business, Notification
from sqlalchemy import and_

class ComplianceService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.state_requirements = {
            'DE': {
                'annual_report': {
                    'due_date': 'March 1',
                    'fee': 300,
                    'requirements': ['business_info', 'registered_agent']
                },
                'franchise_tax': {
                    'due_date': 'March 1',
                    'requirements': ['tax_calculation']
                }
            },
            'WY': {
                'annual_report': {
                    'due_date': 'First day of anniversary month',
                    'fee': 50,
                    'requirements': ['business_info', 'principal_address']
                }
            },
            # Add more states as needed
        }

    def initialize_compliance_calendar(self, business_id):
        """Set up initial compliance calendar for a new business."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        state_reqs = self.state_requirements.get(business.state, {})
        formation_date = business.created_at

        # Add annual report requirement
        if 'annual_report' in state_reqs:
            self._add_annual_report_requirement(business, formation_date)

        # Add franchise tax requirement if applicable
        if 'franchise_tax' in state_reqs:
            self._add_franchise_tax_requirement(business, formation_date)

        # Add initial compliance items
        self._add_initial_compliance_items(business)

        self.db_session.commit()

    def _add_annual_report_requirement(self, business, formation_date):
        """Add annual report compliance item."""
        state_reqs = self.state_requirements[business.state]['annual_report']
        
        if business.state == 'DE':
            due_date = datetime(formation_date.year + 1, 3, 1)
        else:
            # Default to anniversary month
            due_date = formation_date.replace(year=formation_date.year + 1)

        compliance_item = ComplianceItem(
            business_id=business.id,
            type='annual_report',
            due_date=due_date,
            description=f"File annual report for {business.name}",
            requirements=state_reqs,
            status='pending'
        )
        self.db_session.add(compliance_item)

    def _add_franchise_tax_requirement(self, business, formation_date):
        """Add franchise tax compliance item."""
        state_reqs = self.state_requirements[business.state]['franchise_tax']
        
        due_date = datetime(formation_date.year + 1, 3, 1)
        
        compliance_item = ComplianceItem(
            business_id=business.id,
            type='franchise_tax',
            due_date=due_date,
            description=f"File franchise tax for {business.name}",
            requirements=state_reqs,
            status='pending'
        )
        self.db_session.add(compliance_item)

    def _add_initial_compliance_items(self, business):
        """Add initial compliance items for a new business."""
        initial_items = [
            {
                'type': 'ein_application',
                'description': 'Apply for Employer Identification Number (EIN)',
                'due_date': business.created_at + timedelta(days=30),
                'requirements': {
                    'documents': ['ss4_form'],
                    'information': ['owner_ssn', 'business_address']
                }
            },
            {
                'type': 'business_license',
                'description': f'Obtain necessary business licenses in {business.state}',
                'due_date': business.created_at + timedelta(days=45),
                'requirements': {
                    'documents': ['application_forms'],
                    'information': ['business_activity', 'location']
                }
            },
            {
                'type': 'bank_account',
                'description': 'Open business bank account',
                'due_date': business.created_at + timedelta(days=15),
                'requirements': {
                    'documents': ['ein_letter', 'articles_of_organization'],
                    'information': ['owner_id', 'business_address']
                }
            }
        ]

        for item in initial_items:
            compliance_item = ComplianceItem(
                business_id=business.id,
                type=item['type'],
                due_date=item['due_date'],
                description=item['description'],
                requirements=item['requirements'],
                status='pending'
            )
            self.db_session.add(compliance_item)

    def check_upcoming_deadlines(self):
        """Check for upcoming compliance deadlines and create notifications."""
        # Get items due in the next 30 days
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        upcoming_items = self.db_session.query(ComplianceItem).filter(
            and_(
                ComplianceItem.status == 'pending',
                ComplianceItem.due_date <= thirty_days_from_now
            )
        ).all()

        for item in upcoming_items:
            business = self.db_session.query(Business).get(item.business_id)
            days_until_due = (item.due_date - datetime.utcnow()).days

            # Create notification based on urgency
            if days_until_due <= 7:
                priority = 'high'
                message = f"URGENT: {item.description} due in {days_until_due} days"
            elif days_until_due <= 14:
                priority = 'medium'
                message = f"Important: {item.description} due in {days_until_due} days"
            else:
                priority = 'normal'
                message = f"Reminder: {item.description} due in {days_until_due} days"

            notification = Notification(
                user_id=business.owner_id,
                type='compliance_deadline',
                content=message,
                priority=priority
            )
            self.db_session.add(notification)

        self.db_session.commit()

    def update_compliance_status(self, compliance_item_id, new_status, notes=None):
        """Update the status of a compliance item."""
        item = self.db_session.query(ComplianceItem).get(compliance_item_id)
        if not item:
            raise ValueError("Compliance item not found")

        item.status = new_status
        if notes:
            item.description += f"\nNotes: {notes}"

        self.db_session.commit()

    def get_compliance_summary(self, business_id):
        """Get a summary of compliance status for a business."""
        items = self.db_session.query(ComplianceItem).filter_by(
            business_id=business_id
        ).all()

        summary = {
            'total_items': len(items),
            'completed': sum(1 for item in items if item.status == 'completed'),
            'pending': sum(1 for item in items if item.status == 'pending'),
            'overdue': sum(1 for item in items if item.status == 'pending' and item.due_date < datetime.utcnow()),
            'upcoming': []
        }

        # Add upcoming items
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        for item in items:
            if item.status == 'pending' and item.due_date <= thirty_days_from_now:
                summary['upcoming'].append({
                    'id': item.id,
                    'description': item.description,
                    'due_date': item.due_date.isoformat(),
                    'days_until_due': (item.due_date - datetime.utcnow()).days
                })

        return summary
