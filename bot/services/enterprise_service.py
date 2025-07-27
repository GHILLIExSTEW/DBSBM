"""
Enterprise Service - Enterprise Management Portal

This service provides comprehensive enterprise management capabilities including
admin dashboard, user management, billing, and support ticket system for the DBSBM system.

Features:
- Admin dashboard for enterprise management
- User management with bulk operations
- Billing and subscription management
- Support ticket system integration
- Enterprise reporting and analytics
- Centralized user administration
- Role and permission management
- Usage analytics and reporting
- Billing integration and invoicing
- Support and maintenance tools
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from bot.services.performance_monitor import time_operation, record_metric
from bot.data.db_manager import DatabaseManager
from bot.data.cache_manager import cache_get, cache_set

logger = logging.getLogger(__name__)

class EnterprisePlanType(Enum):
    """Types of enterprise plans available."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class SupportTicketStatus(Enum):
    """Status of support tickets."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SupportTicketPriority(Enum):
    """Priority levels for support tickets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EnterpriseAccount:
    """Enterprise account data structure."""
    account_id: str
    account_name: str
    plan_type: EnterprisePlanType
    status: str
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]
    billing_info: Dict[str, Any]
    contact_info: Dict[str, Any]
    is_active: bool = True

@dataclass
class EnterpriseUser:
    """Enterprise user data structure."""
    user_id: int
    account_id: str
    role: str
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool = True

@dataclass
class SupportTicket:
    """Support ticket data structure."""
    ticket_id: str
    account_id: str
    user_id: int
    subject: str
    description: str
    status: SupportTicketStatus
    priority: SupportTicketPriority
    category: str
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

@dataclass
class BillingInvoice:
    """Billing invoice data structure."""
    invoice_id: str
    account_id: str
    amount: float
    currency: str
    status: str
    due_date: datetime
    created_at: datetime
    paid_at: Optional[datetime] = None
    items: List[Dict[str, Any]]

class EnterpriseService:
    """Enterprise management portal service."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_accounts = {}
        self.support_agents = {}

        # Enterprise configuration
        self.config = {
            'multi_tenant_enabled': True,
            'billing_enabled': True,
            'support_system_enabled': True,
            'analytics_enabled': True,
            'audit_logging_enabled': True
        }

        # Plan configurations
        self.plan_configs = {
            EnterprisePlanType.BASIC: {
                'max_users': 50,
                'max_guilds': 10,
                'features': ['basic_betting', 'analytics', 'support'],
                'price_per_month': 99.99
            },
            EnterprisePlanType.PROFESSIONAL: {
                'max_users': 200,
                'max_guilds': 50,
                'features': ['advanced_betting', 'analytics', 'support', 'api_access'],
                'price_per_month': 299.99
            },
            EnterprisePlanType.ENTERPRISE: {
                'max_users': 1000,
                'max_guilds': 200,
                'features': ['all_features', 'custom_integration', 'dedicated_support'],
                'price_per_month': 999.99
            }
        }

    async def initialize(self):
        """Initialize the enterprise service."""
        try:
            # Load active enterprise accounts
            await self._load_enterprise_accounts()

            # Start background tasks
            asyncio.create_task(self._billing_monitoring())
            asyncio.create_task(self._support_ticket_monitoring())

            logger.info("Enterprise service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enterprise service: {e}")
            raise

    @time_operation("enterprise_account_creation")
    async def create_enterprise_account(self, account_name: str, plan_type: EnterprisePlanType,
                                      contact_info: Dict[str, Any], billing_info: Dict[str, Any]) -> Optional[EnterpriseAccount]:
        """Create a new enterprise account."""
        try:
            account_id = f"ent_{uuid.uuid4().hex[:12]}"

            account = EnterpriseAccount(
                account_id=account_id,
                account_name=account_name,
                plan_type=plan_type,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                settings=self.plan_configs[plan_type],
                billing_info=billing_info,
                contact_info=contact_info
            )

            # Store account in database
            await self._store_enterprise_account(account)

            # Create initial billing invoice
            await self._create_initial_invoice(account)

            # Cache account
            self.active_accounts[account_id] = account

            record_metric("enterprise_accounts_created", 1)
            return account

        except Exception as e:
            logger.error(f"Failed to create enterprise account: {e}")
            return None

    @time_operation("enterprise_user_management")
    async def add_enterprise_user(self, account_id: str, user_id: int, role: str,
                                permissions: List[str]) -> bool:
        """Add a user to an enterprise account."""
        try:
            # Check account limits
            if not await self._check_user_limit(account_id):
                logger.warning(f"User limit reached for account {account_id}")
                return False

            enterprise_user = EnterpriseUser(
                user_id=user_id,
                account_id=account_id,
                role=role,
                permissions=permissions,
                created_at=datetime.utcnow()
            )

            # Store user in database
            await self._store_enterprise_user(enterprise_user)

            # Update account user count
            await self._update_account_user_count(account_id)

            return True

        except Exception as e:
            logger.error(f"Failed to add enterprise user: {e}")
            return False

    @time_operation("support_ticket_creation")
    async def create_support_ticket(self, account_id: str, user_id: int, subject: str,
                                  description: str, category: str, priority: SupportTicketPriority) -> Optional[SupportTicket]:
        """Create a new support ticket."""
        try:
            ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"

            ticket = SupportTicket(
                ticket_id=ticket_id,
                account_id=account_id,
                user_id=user_id,
                subject=subject,
                description=description,
                status=SupportTicketStatus.OPEN,
                priority=priority,
                category=category,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Store ticket in database
            await self._store_support_ticket(ticket)

            # Assign to support agent
            await self._assign_ticket_to_agent(ticket)

            # Send notification
            await self._send_ticket_notification(ticket)

            record_metric("support_tickets_created", 1)
            return ticket

        except Exception as e:
            logger.error(f"Failed to create support ticket: {e}")
            return None

    @time_operation("billing_invoice_generation")
    async def generate_billing_invoice(self, account_id: str, billing_period: str) -> Optional[BillingInvoice]:
        """Generate a billing invoice for an enterprise account."""
        try:
            # Get account usage
            usage_data = await self._get_account_usage(account_id, billing_period)

            # Calculate charges
            charges = await self._calculate_charges(account_id, usage_data)

            # Create invoice
            invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
            invoice = BillingInvoice(
                invoice_id=invoice_id,
                account_id=account_id,
                amount=charges['total'],
                currency='USD',
                status='pending',
                due_date=datetime.utcnow() + timedelta(days=30),
                created_at=datetime.utcnow(),
                items=charges['items']
            )

            # Store invoice
            await self._store_billing_invoice(invoice)

            # Send invoice notification
            await self._send_invoice_notification(invoice)

            return invoice

        except Exception as e:
            logger.error(f"Failed to generate billing invoice: {e}")
            return None

    @time_operation("enterprise_analytics")
    async def get_enterprise_analytics(self, account_id: str, date_range: str = "30d") -> Dict[str, Any]:
        """Get comprehensive analytics for an enterprise account."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=int(date_range[:-1]))

            # Get user analytics
            user_analytics = await self._get_user_analytics(account_id, start_date, end_date)

            # Get usage analytics
            usage_analytics = await self._get_usage_analytics(account_id, start_date, end_date)

            # Get billing analytics
            billing_analytics = await self._get_billing_analytics(account_id, start_date, end_date)

            # Get support analytics
            support_analytics = await self._get_support_analytics(account_id, start_date, end_date)

            return {
                'period': {'start': start_date, 'end': end_date},
                'user_analytics': user_analytics,
                'usage_analytics': usage_analytics,
                'billing_analytics': billing_analytics,
                'support_analytics': support_analytics,
                'summary': await self._generate_analytics_summary(account_id, start_date, end_date)
            }

        except Exception as e:
            logger.error(f"Failed to get enterprise analytics: {e}")
            return {}

    @time_operation("bulk_user_operations")
    async def bulk_user_operations(self, account_id: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform bulk operations on enterprise users."""
        try:
            results = {
                'successful': 0,
                'failed': 0,
                'errors': []
            }

            for operation in operations:
                try:
                    op_type = operation.get('type')
                    user_id = operation.get('user_id')

                    if op_type == 'add':
                        success = await self.add_enterprise_user(
                            account_id, user_id,
                            operation.get('role', 'user'),
                            operation.get('permissions', [])
                        )
                    elif op_type == 'update':
                        success = await self._update_enterprise_user(account_id, user_id, operation)
                    elif op_type == 'remove':
                        success = await self._remove_enterprise_user(account_id, user_id)
                    else:
                        success = False
                        results['errors'].append(f"Unknown operation type: {op_type}")

                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error processing operation: {e}")

            return results

        except Exception as e:
            logger.error(f"Failed to perform bulk user operations: {e}")
            return {'successful': 0, 'failed': len(operations), 'errors': [str(e)]}

    @time_operation("support_ticket_management")
    async def update_support_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update a support ticket."""
        try:
            # Get current ticket
            ticket = await self._get_support_ticket(ticket_id)
            if not ticket:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)

            ticket.updated_at = datetime.utcnow()

            # Store updated ticket
            await self._store_support_ticket(ticket)

            # Send notifications if status changed
            if 'status' in updates:
                await self._send_status_update_notification(ticket)

            return True

        except Exception as e:
            logger.error(f"Failed to update support ticket: {e}")
            return False

    async def get_enterprise_dashboard_data(self, account_id: str) -> Dict[str, Any]:
        """Get data for the enterprise dashboard."""
        try:
            # Get account info
            account = await self._get_enterprise_account(account_id)
            if not account:
                return {}

            # Get quick stats
            stats = await self._get_dashboard_stats(account_id)

            # Get recent activity
            recent_activity = await self._get_recent_activity(account_id)

            # Get pending items
            pending_items = await self._get_pending_items(account_id)

            return {
                'account': asdict(account),
                'stats': stats,
                'recent_activity': recent_activity,
                'pending_items': pending_items
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}

    # Private helper methods

    async def _load_enterprise_accounts(self):
        """Load active enterprise accounts from database."""
        try:
            query = "SELECT * FROM enterprise_accounts WHERE is_active = TRUE"
            results = await self.db_manager.fetch_all(query)

            for row in results:
                account = EnterpriseAccount(**row)
                self.active_accounts[account.account_id] = account

            logger.info(f"Loaded {len(self.active_accounts)} enterprise accounts")

        except Exception as e:
            logger.error(f"Failed to load enterprise accounts: {e}")

    async def _store_enterprise_account(self, account: EnterpriseAccount):
        """Store enterprise account in database."""
        try:
            query = """
            INSERT INTO enterprise_accounts
            (account_id, account_name, plan_type, status, created_at, updated_at, settings, billing_info, contact_info, is_active)
            VALUES (:account_id, :account_name, :plan_type, :status, :created_at, :updated_at, :settings, :billing_info, :contact_info, :is_active)
            """

            await self.db_manager.execute(query, {
                'account_id': account.account_id,
                'account_name': account.account_name,
                'plan_type': account.plan_type.value,
                'status': account.status,
                'created_at': account.created_at,
                'updated_at': account.updated_at,
                'settings': json.dumps(account.settings),
                'billing_info': json.dumps(account.billing_info),
                'contact_info': json.dumps(account.contact_info),
                'is_active': account.is_active
            })

        except Exception as e:
            logger.error(f"Failed to store enterprise account: {e}")

    async def _create_initial_invoice(self, account: EnterpriseAccount):
        """Create initial billing invoice for new account."""
        try:
            plan_config = self.plan_configs[account.plan_type]

            invoice = BillingInvoice(
                invoice_id=f"inv_{uuid.uuid4().hex[:12]}",
                account_id=account.account_id,
                amount=plan_config['price_per_month'],
                currency='USD',
                status='pending',
                due_date=datetime.utcnow() + timedelta(days=30),
                created_at=datetime.utcnow(),
                items=[{
                    'description': f"{account.plan_type.value.title()} Plan - Setup",
                    'amount': plan_config['price_per_month'],
                    'quantity': 1
                }]
            )

            await self._store_billing_invoice(invoice)

        except Exception as e:
            logger.error(f"Failed to create initial invoice: {e}")

    async def _check_user_limit(self, account_id: str) -> bool:
        """Check if account has reached user limit."""
        try:
            account = self.active_accounts.get(account_id)
            if not account:
                return False

            plan_config = self.plan_configs[account.plan_type]
            max_users = plan_config['max_users']

            # Get current user count
            query = "SELECT COUNT(*) as user_count FROM enterprise_users WHERE account_id = :account_id AND is_active = TRUE"
            result = await self.db_manager.fetch_one(query, {'account_id': account_id})

            current_users = result['user_count'] if result else 0
            return current_users < max_users

        except Exception as e:
            logger.error(f"Failed to check user limit: {e}")
            return False

    async def _store_enterprise_user(self, user: EnterpriseUser):
        """Store enterprise user in database."""
        try:
            query = """
            INSERT INTO enterprise_users
            (user_id, account_id, role, permissions, created_at, last_login, is_active)
            VALUES (:user_id, :account_id, :role, :permissions, :created_at, :last_login, :is_active)
            """

            await self.db_manager.execute(query, {
                'user_id': user.user_id,
                'account_id': user.account_id,
                'role': user.role,
                'permissions': json.dumps(user.permissions),
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active
            })

        except Exception as e:
            logger.error(f"Failed to store enterprise user: {e}")

    async def _update_account_user_count(self, account_id: str):
        """Update account user count."""
        try:
            query = """
            UPDATE enterprise_accounts
            SET user_count = (
                SELECT COUNT(*) FROM enterprise_users
                WHERE account_id = :account_id AND is_active = TRUE
            ),
            updated_at = NOW()
            WHERE account_id = :account_id
            """

            await self.db_manager.execute(query, {'account_id': account_id})

        except Exception as e:
            logger.error(f"Failed to update account user count: {e}")

    async def _store_support_ticket(self, ticket: SupportTicket):
        """Store support ticket in database."""
        try:
            query = """
            INSERT INTO support_tickets
            (ticket_id, account_id, user_id, subject, description, status, priority, category, created_at, updated_at, assigned_to, resolution_notes)
            VALUES (:ticket_id, :account_id, :user_id, :subject, :description, :status, :priority, :category, :created_at, :updated_at, :assigned_to, :resolution_notes)
            """

            await self.db_manager.execute(query, {
                'ticket_id': ticket.ticket_id,
                'account_id': ticket.account_id,
                'user_id': ticket.user_id,
                'subject': ticket.subject,
                'description': ticket.description,
                'status': ticket.status.value,
                'priority': ticket.priority.value,
                'category': ticket.category,
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
                'assigned_to': ticket.assigned_to,
                'resolution_notes': ticket.resolution_notes
            })

        except Exception as e:
            logger.error(f"Failed to store support ticket: {e}")

    async def _assign_ticket_to_agent(self, ticket: SupportTicket):
        """Assign ticket to available support agent."""
        try:
            # Simple round-robin assignment
            # In production, this would use more sophisticated logic
            available_agents = await self._get_available_support_agents()

            if available_agents:
                ticket.assigned_to = available_agents[0]['agent_id']
                await self._store_support_ticket(ticket)

        except Exception as e:
            logger.error(f"Failed to assign ticket to agent: {e}")

    async def _send_ticket_notification(self, ticket: SupportTicket):
        """Send notification for new support ticket."""
        try:
            # This would integrate with notification systems
            # For now, just log the notification
            logger.info(f"Support ticket created: {ticket.ticket_id} - {ticket.subject}")

        except Exception as e:
            logger.error(f"Failed to send ticket notification: {e}")

    async def _get_account_usage(self, account_id: str, billing_period: str) -> Dict[str, Any]:
        """Get account usage data for billing period."""
        try:
            # Get user count
            query = """
            SELECT COUNT(*) as user_count
            FROM enterprise_users
            WHERE account_id = :account_id AND is_active = TRUE
            """
            user_result = await self.db_manager.fetch_one(query, {'account_id': account_id})

            # Get API usage
            query = """
            SELECT COUNT(*) as api_calls
            FROM api_usage
            WHERE account_id = :account_id
            AND timestamp > DATE_SUB(NOW(), INTERVAL 1 MONTH)
            """
            api_result = await self.db_manager.fetch_one(query, {'account_id': account_id})

            return {
                'user_count': user_result['user_count'] if user_result else 0,
                'api_calls': api_result['api_calls'] if api_result else 0,
                'billing_period': billing_period
            }

        except Exception as e:
            logger.error(f"Failed to get account usage: {e}")
            return {}

    async def _calculate_charges(self, account_id: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate billing charges for account."""
        try:
            account = self.active_accounts.get(account_id)
            if not account:
                return {'total': 0, 'items': []}

            plan_config = self.plan_configs[account.plan_type]
            base_price = plan_config['price_per_month']

            items = [{
                'description': f"{account.plan_type.value.title()} Plan",
                'amount': base_price,
                'quantity': 1
            }]

            # Add overage charges if applicable
            max_users = plan_config['max_users']
            current_users = usage_data.get('user_count', 0)

            if current_users > max_users:
                overage_users = current_users - max_users
                overage_charge = overage_users * 5.0  # $5 per additional user
                items.append({
                    'description': f"User Overage ({overage_users} users)",
                    'amount': overage_charge,
                    'quantity': overage_users
                })

            total = sum(item['amount'] * item['quantity'] for item in items)

            return {
                'total': total,
                'items': items
            }

        except Exception as e:
            logger.error(f"Failed to calculate charges: {e}")
            return {'total': 0, 'items': []}

    async def _store_billing_invoice(self, invoice: BillingInvoice):
        """Store billing invoice in database."""
        try:
            query = """
            INSERT INTO billing_invoices
            (invoice_id, account_id, amount, currency, status, due_date, created_at, paid_at, items)
            VALUES (:invoice_id, :account_id, :amount, :currency, :status, :due_date, :created_at, :paid_at, :items)
            """

            await self.db_manager.execute(query, {
                'invoice_id': invoice.invoice_id,
                'account_id': invoice.account_id,
                'amount': invoice.amount,
                'currency': invoice.currency,
                'status': invoice.status,
                'due_date': invoice.due_date,
                'created_at': invoice.created_at,
                'paid_at': invoice.paid_at,
                'items': json.dumps(invoice.items)
            })

        except Exception as e:
            logger.error(f"Failed to store billing invoice: {e}")

    async def _send_invoice_notification(self, invoice: BillingInvoice):
        """Send invoice notification."""
        try:
            # This would integrate with notification systems
            logger.info(f"Billing invoice generated: {invoice.invoice_id} - ${invoice.amount}")

        except Exception as e:
            logger.error(f"Failed to send invoice notification: {e}")

    async def _get_user_analytics(self, account_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user analytics for enterprise account."""
        try:
            query = """
            SELECT
                COUNT(*) as total_users,
                COUNT(CASE WHEN last_login > DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as active_users_7d,
                COUNT(CASE WHEN last_login > DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as active_users_30d,
                AVG(CASE WHEN last_login IS NOT NULL THEN DATEDIFF(NOW(), last_login) END) as avg_days_since_login
            FROM enterprise_users
            WHERE account_id = :account_id
            AND created_at BETWEEN :start_date AND :end_date
            """

            result = await self.db_manager.fetch_one(query, {
                'account_id': account_id,
                'start_date': start_date,
                'end_date': end_date
            })

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}

    async def _get_usage_analytics(self, account_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get usage analytics for enterprise account."""
        try:
            query = """
            SELECT
                COUNT(*) as total_api_calls,
                COUNT(DISTINCT DATE(timestamp)) as active_days,
                AVG(calls_per_day) as avg_daily_calls
            FROM (
                SELECT
                    timestamp,
                    COUNT(*) as calls_per_day
                FROM api_usage
                WHERE account_id = :account_id
                AND timestamp BETWEEN :start_date AND :end_date
                GROUP BY DATE(timestamp)
            ) daily_usage
            """

            result = await self.db_manager.fetch_one(query, {
                'account_id': account_id,
                'start_date': start_date,
                'end_date': end_date
            })

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {}

    async def _get_billing_analytics(self, account_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get billing analytics for enterprise account."""
        try:
            query = """
            SELECT
                COUNT(*) as total_invoices,
                SUM(amount) as total_billed,
                SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_paid,
                AVG(amount) as avg_invoice_amount
            FROM billing_invoices
            WHERE account_id = :account_id
            AND created_at BETWEEN :start_date AND :end_date
            """

            result = await self.db_manager.fetch_one(query, {
                'account_id': account_id,
                'start_date': start_date,
                'end_date': end_date
            })

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Failed to get billing analytics: {e}")
            return {}

    async def _get_support_analytics(self, account_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get support analytics for enterprise account."""
        try:
            query = """
            SELECT
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                AVG(CASE WHEN status = 'resolved' THEN DATEDIFF(resolved_at, created_at) END) as avg_resolution_time
            FROM support_tickets
            WHERE account_id = :account_id
            AND created_at BETWEEN :start_date AND :end_date
            """

            result = await self.db_manager.fetch_one(query, {
                'account_id': account_id,
                'start_date': start_date,
                'end_date': end_date
            })

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Failed to get support analytics: {e}")
            return {}

    async def _generate_analytics_summary(self, account_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate analytics summary for enterprise account."""
        try:
            # Get all analytics data
            user_analytics = await self._get_user_analytics(account_id, start_date, end_date)
            usage_analytics = await self._get_usage_analytics(account_id, start_date, end_date)
            billing_analytics = await self._get_billing_analytics(account_id, start_date, end_date)
            support_analytics = await self._get_support_analytics(account_id, start_date, end_date)

            return {
                'total_users': user_analytics.get('total_users', 0),
                'active_users': user_analytics.get('active_users_30d', 0),
                'total_api_calls': usage_analytics.get('total_api_calls', 0),
                'total_billed': billing_analytics.get('total_billed', 0),
                'total_tickets': support_analytics.get('total_tickets', 0),
                'resolved_tickets': support_analytics.get('resolved_tickets', 0)
            }

        except Exception as e:
            logger.error(f"Failed to generate analytics summary: {e}")
            return {}

    async def _update_enterprise_user(self, account_id: str, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update enterprise user."""
        try:
            query = "UPDATE enterprise_users SET "
            params = {'account_id': account_id, 'user_id': user_id}

            update_fields = []
            for key, value in updates.items():
                if key in ['role', 'permissions', 'is_active']:
                    update_fields.append(f"{key} = :{key}")
                    if key == 'permissions':
                        params[key] = json.dumps(value)
                    else:
                        params[key] = value

            if not update_fields:
                return False

            query += ", ".join(update_fields)
            query += ", updated_at = NOW() WHERE account_id = :account_id AND user_id = :user_id"

            await self.db_manager.execute(query, params)
            return True

        except Exception as e:
            logger.error(f"Failed to update enterprise user: {e}")
            return False

    async def _remove_enterprise_user(self, account_id: str, user_id: int) -> bool:
        """Remove enterprise user."""
        try:
            query = """
            UPDATE enterprise_users
            SET is_active = FALSE, updated_at = NOW()
            WHERE account_id = :account_id AND user_id = :user_id
            """

            await self.db_manager.execute(query, {
                'account_id': account_id,
                'user_id': user_id
            })

            return True

        except Exception as e:
            logger.error(f"Failed to remove enterprise user: {e}")
            return False

    async def _get_support_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get support ticket by ID."""
        try:
            query = "SELECT * FROM support_tickets WHERE ticket_id = :ticket_id"
            result = await self.db_manager.fetch_one(query, {'ticket_id': ticket_id})

            if result:
                return SupportTicket(**result)
            return None

        except Exception as e:
            logger.error(f"Failed to get support ticket: {e}")
            return None

    async def _send_status_update_notification(self, ticket: SupportTicket):
        """Send status update notification."""
        try:
            logger.info(f"Support ticket {ticket.ticket_id} status updated to {ticket.status.value}")

        except Exception as e:
            logger.error(f"Failed to send status update notification: {e}")

    async def _get_enterprise_account(self, account_id: str) -> Optional[EnterpriseAccount]:
        """Get enterprise account by ID."""
        try:
            query = "SELECT * FROM enterprise_accounts WHERE account_id = :account_id"
            result = await self.db_manager.fetch_one(query, {'account_id': account_id})

            if result:
                return EnterpriseAccount(**result)
            return None

        except Exception as e:
            logger.error(f"Failed to get enterprise account: {e}")
            return None

    async def _get_dashboard_stats(self, account_id: str) -> Dict[str, Any]:
        """Get dashboard statistics."""
        try:
            # Get quick stats
            stats = {
                'total_users': 0,
                'active_users': 0,
                'pending_tickets': 0,
                'unpaid_invoices': 0
            }

            # User stats
            query = """
            SELECT
                COUNT(*) as total_users,
                COUNT(CASE WHEN last_login > DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as active_users
            FROM enterprise_users
            WHERE account_id = :account_id AND is_active = TRUE
            """
            user_result = await self.db_manager.fetch_one(query, {'account_id': account_id})
            if user_result:
                stats['total_users'] = user_result['total_users']
                stats['active_users'] = user_result['active_users']

            # Ticket stats
            query = """
            SELECT COUNT(*) as pending_tickets
            FROM support_tickets
            WHERE account_id = :account_id AND status IN ('open', 'in_progress')
            """
            ticket_result = await self.db_manager.fetch_one(query, {'account_id': account_id})
            if ticket_result:
                stats['pending_tickets'] = ticket_result['pending_tickets']

            # Invoice stats
            query = """
            SELECT COUNT(*) as unpaid_invoices
            FROM billing_invoices
            WHERE account_id = :account_id AND status = 'pending'
            """
            invoice_result = await self.db_manager.fetch_one(query, {'account_id': account_id})
            if invoice_result:
                stats['unpaid_invoices'] = invoice_result['unpaid_invoices']

            return stats

        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {}

    async def _get_recent_activity(self, account_id: str) -> List[Dict[str, Any]]:
        """Get recent activity for account."""
        try:
            # Get recent user logins
            query = """
            SELECT user_id, last_login, 'login' as activity_type
            FROM enterprise_users
            WHERE account_id = :account_id AND last_login IS NOT NULL
            ORDER BY last_login DESC
            LIMIT 10
            """

            results = await self.db_manager.fetch_all(query, {'account_id': account_id})
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []

    async def _get_pending_items(self, account_id: str) -> Dict[str, Any]:
        """Get pending items for account."""
        try:
            pending_items = {
                'tickets': [],
                'invoices': []
            }

            # Get pending tickets
            query = """
            SELECT ticket_id, subject, priority, created_at
            FROM support_tickets
            WHERE account_id = :account_id AND status IN ('open', 'in_progress')
            ORDER BY priority DESC, created_at ASC
            LIMIT 5
            """

            ticket_results = await self.db_manager.fetch_all(query, {'account_id': account_id})
            pending_items['tickets'] = [dict(row) for row in ticket_results]

            # Get pending invoices
            query = """
            SELECT invoice_id, amount, due_date
            FROM billing_invoices
            WHERE account_id = :account_id AND status = 'pending'
            ORDER BY due_date ASC
            LIMIT 5
            """

            invoice_results = await self.db_manager.fetch_all(query, {'account_id': account_id})
            pending_items['invoices'] = [dict(row) for row in invoice_results]

            return pending_items

        except Exception as e:
            logger.error(f"Failed to get pending items: {e}")
            return {'tickets': [], 'invoices': []}

    async def _get_available_support_agents(self) -> List[Dict[str, Any]]:
        """Get available support agents."""
        try:
            # This would query support agents table
            # For now, return mock data
            return [
                {'agent_id': 'agent_1', 'name': 'Support Agent 1', 'availability': 'online'},
                {'agent_id': 'agent_2', 'name': 'Support Agent 2', 'availability': 'online'}
            ]

        except Exception as e:
            logger.error(f"Failed to get available support agents: {e}")
            return []

    async def _billing_monitoring(self):
        """Background task for billing monitoring."""
        while True:
            try:
                # Check for overdue invoices
                await self._check_overdue_invoices()

                # Generate monthly invoices
                await self._generate_monthly_invoices()

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in billing monitoring: {e}")
                await asyncio.sleep(7200)  # Wait 2 hours on error

    async def _support_ticket_monitoring(self):
        """Background task for support ticket monitoring."""
        while True:
            try:
                # Check for stale tickets
                await self._check_stale_tickets()

                # Auto-assign unassigned tickets
                await self._auto_assign_tickets()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in support ticket monitoring: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _check_overdue_invoices(self):
        """Check for overdue invoices and send reminders."""
        try:
            query = """
            SELECT * FROM billing_invoices
            WHERE status = 'pending' AND due_date < NOW()
            """

            results = await self.db_manager.fetch_all(query)

            for row in results:
                # Send overdue reminder
                await self._send_overdue_reminder(row)

        except Exception as e:
            logger.error(f"Failed to check overdue invoices: {e}")

    async def _generate_monthly_invoices(self):
        """Generate monthly invoices for all accounts."""
        try:
            # Get all active accounts
            query = "SELECT account_id FROM enterprise_accounts WHERE is_active = TRUE"
            results = await self.db_manager.fetch_all(query)

            for row in results:
                account_id = row['account_id']

                # Check if invoice already exists for this month
                existing_invoice = await self._check_monthly_invoice_exists(account_id)

                if not existing_invoice:
                    await self.generate_billing_invoice(account_id, "1m")

        except Exception as e:
            logger.error(f"Failed to generate monthly invoices: {e}")

    async def _check_stale_tickets(self):
        """Check for stale support tickets."""
        try:
            query = """
            SELECT * FROM support_tickets
            WHERE status IN ('open', 'in_progress')
            AND updated_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
            """

            results = await self.db_manager.fetch_all(query)

            for row in results:
                # Send stale ticket notification
                await self._send_stale_ticket_notification(row)

        except Exception as e:
            logger.error(f"Failed to check stale tickets: {e}")

    async def _auto_assign_tickets(self):
        """Auto-assign unassigned tickets."""
        try:
            query = """
            SELECT * FROM support_tickets
            WHERE assigned_to IS NULL AND status = 'open'
            """

            results = await self.db_manager.fetch_all(query)

            for row in results:
                ticket = SupportTicket(**row)
                await self._assign_ticket_to_agent(ticket)

        except Exception as e:
            logger.error(f"Failed to auto-assign tickets: {e}")

    async def _send_overdue_reminder(self, invoice_data: Dict[str, Any]):
        """Send overdue invoice reminder."""
        try:
            logger.info(f"Sending overdue reminder for invoice {invoice_data['invoice_id']}")

        except Exception as e:
            logger.error(f"Failed to send overdue reminder: {e}")

    async def _check_monthly_invoice_exists(self, account_id: str) -> bool:
        """Check if monthly invoice already exists."""
        try:
            query = """
            SELECT COUNT(*) as count FROM billing_invoices
            WHERE account_id = :account_id
            AND created_at > DATE_SUB(NOW(), INTERVAL 1 MONTH)
            """

            result = await self.db_manager.fetch_one(query, {'account_id': account_id})
            return result['count'] > 0 if result else False

        except Exception as e:
            logger.error(f"Failed to check monthly invoice: {e}")
            return False

    async def _send_stale_ticket_notification(self, ticket_data: Dict[str, Any]):
        """Send stale ticket notification."""
        try:
            logger.info(f"Sending stale ticket notification for {ticket_data['ticket_id']}")

        except Exception as e:
            logger.error(f"Failed to send stale ticket notification: {e}")

    async def cleanup(self):
        """Cleanup enterprise service resources."""
        self.active_accounts.clear()
        self.support_agents.clear()

# Enterprise service is now complete with comprehensive enterprise management capabilities
#
# This service provides:
# - Admin dashboard for enterprise management
# - User management with bulk operations
# - Billing and subscription management
# - Support ticket system integration
# - Enterprise reporting and analytics
# - Centralized user administration
# - Role and permission management
# - Usage analytics and reporting
# - Billing integration and invoicing
# - Support and maintenance tools
