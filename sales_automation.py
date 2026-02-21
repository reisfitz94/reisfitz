"""
Sales Automation System
A Python program to automate the sales process for a technology company.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict
from decimal import Decimal
import uuid
import json


class LeadStatus(Enum):
    """Lead status in the sales pipeline"""
    NEW = "new"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealStage(Enum):
    """Stages of a deal in the sales pipeline"""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    CLOSED = "closed"


class SalesProductType(Enum):
    """Types of products/services sold"""
    SAAS = "SaaS"
    CONSULTING = "Consulting"
    ENTERPRISE_LICENSE = "Enterprise License"
    SUPPORT = "Support"


@dataclass
class SalesRep:
    """Represents a sales representative"""
    rep_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    email: str = ""
    phone: str = ""
    region: str = ""
    commission_rate: Decimal = Decimal("0.05")  # 5% default
    quota: Decimal = Decimal("0")
    
    def __post_init__(self):
        self.commission_rate = Decimal(str(self.commission_rate))
        self.quota = Decimal(str(self.quota))


@dataclass
class Customer:
    """Represents a customer"""
    customer_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    company_name: str = ""
    industry: str = ""
    company_size: str = ""  # Small, Medium, Large, Enterprise
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    lifetime_value: Decimal = Decimal("0")
    
    def __post_init__(self):
        self.lifetime_value = Decimal(str(self.lifetime_value))


@dataclass
class Lead:
    """Represents a sales lead"""
    lead_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    company_name: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    industry: str = ""
    status: LeadStatus = LeadStatus.NEW
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_contact: Optional[datetime] = None
    notes: str = ""
    
    def __str__(self) -> str:
        return f"Lead({self.company_name}, Status: {self.status.value}, Assigned: {self.assigned_to})"


@dataclass
class Product:
    """Represents a product/service"""
    product_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    product_type: SalesProductType = SalesProductType.SAAS
    price: Decimal = Decimal("0")
    description: str = ""
    license_term: int = 1  # in months
    
    def __post_init__(self):
        self.price = Decimal(str(self.price))


@dataclass
class Deal:
    """Represents a sales deal/opportunity"""
    deal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    lead_id: str = ""
    customer_id: str = ""
    opportunity_name: str = ""
    description: str = ""
    products: List[Product] = field(default_factory=list)
    amount: Decimal = Decimal("0")
    stage: DealStage = DealStage.PROSPECTING
    probability: int = 10  # 10-100
    assigned_to: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.amount = Decimal(str(self.amount))
    
    def calculate_weighted_value(self) -> Decimal:
        """Calculate deal value weighted by probability"""
        return self.amount * Decimal(self.probability) / Decimal(100)
    
    def __str__(self) -> str:
        return f"Deal({self.opportunity_name}, Stage: {self.stage.value}, Amount: ${self.amount})"


@dataclass
class Quote:
    """Represents a sales quote"""
    quote_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    deal_id: str = ""
    customer_id: str = ""
    issued_date: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    items: List[tuple] = field(default_factory=list)  # (product, quantity, unit_price)
    subtotal: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0.1")  # 10%
    discount: Decimal = Decimal("0")
    status: str = "draft"  # draft, sent, accepted, rejected
    
    def __post_init__(self):
        self.tax_rate = Decimal(str(self.tax_rate))
        self.discount = Decimal(str(self.discount))
    
    def add_item(self, product: Product, quantity: int, unit_price: Optional[Decimal] = None):
        """Add an item to the quote"""
        price = unit_price or product.price
        self.items.append((product, quantity, Decimal(str(price))))
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calculate quote totals"""
        self.subtotal = sum(qty * price for _, qty, price in self.items)
        self.subtotal -= self.discount
    
    def get_tax(self) -> Decimal:
        """Calculate tax amount"""
        return self.subtotal * self.tax_rate
    
    def get_total(self) -> Decimal:
        """Get total quote amount"""
        return self.subtotal + self.get_tax()
    
    def __str__(self) -> str:
        return f"Quote(ID: {self.quote_id}, Total: ${self.get_total():.2f}, Status: {self.status})"


class SalesAutomationSystem:
    """Main sales automation system"""
    
    def __init__(self, company_name: str):
        self.company_name = company_name
        self.sales_reps: Dict[str, SalesRep] = {}
        self.customers: Dict[str, Customer] = {}
        self.leads: Dict[str, Lead] = {}
        self.deals: Dict[str, Deal] = {}
        self.products: Dict[str, Product] = {}
        self.quotes: Dict[str, Quote] = {}
    
    # Sales Rep Management
    def add_sales_rep(self, name: str, email: str, phone: str, region: str, 
                     commission_rate: Decimal, quota: Decimal) -> SalesRep:
        """Add a new sales representative"""
        rep = SalesRep(
            name=name,
            email=email,
            phone=phone,
            region=region,
            commission_rate=commission_rate,
            quota=quota
        )
        self.sales_reps[rep.rep_id] = rep
        return rep
    
    # Customer Management
    def add_customer(self, company_name: str, industry: str, company_size: str,
                    contact_person: str, email: str, phone: str, address: str) -> Customer:
        """Add a new customer"""
        customer = Customer(
            company_name=company_name,
            industry=industry,
            company_size=company_size,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address
        )
        self.customers[customer.customer_id] = customer
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Retrieve a customer"""
        return self.customers.get(customer_id)
    
    # Lead Management
    def create_lead(self, company_name: str, contact_person: str, email: str,
                   phone: str, industry: str, notes: str = "") -> Lead:
        """Create a new lead"""
        lead = Lead(
            company_name=company_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            industry=industry,
            notes=notes
        )
        self.leads[lead.lead_id] = lead
        return lead
    
    def assign_lead(self, lead_id: str, rep_id: str) -> bool:
        """Assign a lead to a sales representative"""
        if lead_id not in self.leads or rep_id not in self.sales_reps:
            return False
        
        self.leads[lead_id].assigned_to = rep_id
        self.leads[lead_id].status = LeadStatus.QUALIFIED
        self.leads[lead_id].last_contact = datetime.now()
        return True
    
    def update_lead_status(self, lead_id: str, status: LeadStatus) -> bool:
        """Update lead status"""
        if lead_id not in self.leads:
            return False
        self.leads[lead_id].status = status
        self.leads[lead_id].last_contact = datetime.now()
        return True
    
    def get_lead_by_status(self, status: LeadStatus) -> List[Lead]:
        """Get all leads with specific status"""
        return [lead for lead in self.leads.values() if lead.status == status]
    
    # Product Management
    def add_product(self, name: str, product_type: SalesProductType, 
                   price: Decimal, description: str, license_term: int = 1) -> Product:
        """Add a new product"""
        product = Product(
            name=name,
            product_type=product_type,
            price=price,
            description=description,
            license_term=license_term
        )
        self.products[product.product_id] = product
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Retrieve a product"""
        return self.products.get(product_id)
    
    # Deal Management
    def create_deal(self, lead_id: str, opportunity_name: str, description: str,
                   amount: Decimal, expected_close_date: datetime) -> Deal:
        """Create a new deal from a lead"""
        if lead_id not in self.leads:
            raise ValueError("Lead not found")
        
        lead = self.leads[lead_id]
        deal = Deal(
            lead_id=lead_id,
            opportunity_name=opportunity_name,
            description=description,
            amount=amount,
            expected_close_date=expected_close_date,
            assigned_to=lead.assigned_to
        )
        self.deals[deal.deal_id] = deal
        return deal
    
    def advance_deal_stage(self, deal_id: str, new_stage: DealStage) -> bool:
        """Move a deal to the next stage"""
        if deal_id not in self.deals:
            return False
        
        deal = self.deals[deal_id]
        deal.stage = new_stage
        
        if new_stage == DealStage.CLOSED:
            deal.actual_close_date = datetime.now()
        
        return True
    
    def update_deal_probability(self, deal_id: str, probability: int) -> bool:
        """Update deal win probability"""
        if deal_id not in self.deals or not (10 <= probability <= 100):
            return False
        
        self.deals[deal_id].probability = probability
        return True
    
    def get_sales_pipeline(self) -> Dict[str, List[Deal]]:
        """Get all deals grouped by stage"""
        pipeline = {stage.value: [] for stage in DealStage}
        
        for deal in self.deals.values():
            pipeline[deal.stage.value].append(deal)
        
        return pipeline
    
    def get_deals_by_rep(self, rep_id: str) -> List[Deal]:
        """Get all deals assigned to a sales rep"""
        return [deal for deal in self.deals.values() if deal.assigned_to == rep_id]
    
    # Quote Management
    def create_quote(self, deal_id: str, customer_id: str, valid_days: int = 30) -> Quote:
        """Create a quote for a deal"""
        if deal_id not in self.deals or customer_id not in self.customers:
            raise ValueError("Deal or Customer not found")
        
        quote = Quote(
            deal_id=deal_id,
            customer_id=customer_id,
            valid_until=datetime.now() + timedelta(days=valid_days)
        )
        self.quotes[quote.quote_id] = quote
        return quote
    
    def add_product_to_quote(self, quote_id: str, product_id: str, quantity: int) -> bool:
        """Add a product to a quote"""
        if quote_id not in self.quotes or product_id not in self.products:
            return False
        
        quote = self.quotes[quote_id]
        product = self.products[product_id]
        quote.add_item(product, quantity)
        return True
    
    def send_quote(self, quote_id: str) -> bool:
        """Send a quote to customer"""
        if quote_id not in self.quotes:
            return False
        
        quote = self.quotes[quote_id]
        quote.status = "sent"
        return True
    
    def accept_quote(self, quote_id: str) -> bool:
        """Accept a quote and convert to customer"""
        if quote_id not in self.quotes:
            return False
        
        quote = self.quotes[quote_id]
        quote.status = "accepted"
        
        # Update deal stage
        if quote.deal_id in self.deals:
            deal = self.deals[quote.deal_id]
            deal.stage = DealStage.CLOSED
            deal.actual_close_date = datetime.now()
            
            # Update customer lifetime value
            if quote.customer_id in self.customers:
                self.customers[quote.customer_id].lifetime_value += quote.get_total()
        
        return True
    
    # Sales Analytics
    def calculate_open_pipeline_value(self) -> Decimal:
        """Calculate total value of open deals"""
        return sum(deal.calculate_weighted_value() 
                  for deal in self.deals.values() 
                  if deal.stage != DealStage.CLOSED)
    
    def calculate_closed_deals_value(self) -> Decimal:
        """Calculate total value of closed deals"""
        return sum(deal.amount for deal in self.deals.values() 
                  if deal.stage == DealStage.CLOSED)
    
    def calculate_rep_commission(self, rep_id: str) -> Decimal:
        """Calculate commission for a sales rep"""
        if rep_id not in self.sales_reps:
            return Decimal("0")
        
        rep = self.sales_reps[rep_id]
        rep_deals = self.get_deals_by_rep(rep_id)
        closed_deals_value = sum(deal.amount for deal in rep_deals 
                                if deal.stage == DealStage.CLOSED)
        
        return closed_deals_value * rep.commission_rate
    
    def get_rep_performance(self, rep_id: str) -> Dict:
        """Get performance metrics for a sales rep"""
        if rep_id not in self.sales_reps:
            return {}
        
        rep = self.sales_reps[rep_id]
        rep_deals = self.get_deals_by_rep(rep_id)
        
        total_value = sum(deal.amount for deal in rep_deals)
        closed_value = sum(deal.amount for deal in rep_deals 
                          if deal.stage == DealStage.CLOSED)
        open_value = total_value - closed_value
        closed_count = len([d for d in rep_deals if d.stage == DealStage.CLOSED])
        
        return {
            'rep_id': rep_id,
            'name': rep.name,
            'total_deals': len(rep_deals),
            'closed_deals': closed_count,
            'win_rate': f"{(closed_count / len(rep_deals) * 100):.1f}%" if rep_deals else "0%",
            'total_pipeline_value': f"${total_value:,.2f}",
            'closed_deals_value': f"${closed_value:,.2f}",
            'open_pipeline_value': f"${open_value:,.2f}",
            'quota': f"${rep.quota:,.2f}",
            'quota_attainment': f"{(closed_value / rep.quota * 100):.1f}%" if rep.quota > 0 else "0%",
            'commission': f"${self.calculate_rep_commission(rep_id):,.2f}"
        }
    
    def print_sales_report(self) -> None:
        """Print comprehensive sales report"""
        print(f"\n{'='*80}")
        print(f"SALES AUTOMATION REPORT - {self.company_name}")
        print(f"{'='*80}\n")
        
        # Overall Metrics
        print(f"{'OVERALL SALES METRICS':-^80}")
        total_pipeline = self.calculate_open_pipeline_value()
        closed_value = self.calculate_closed_deals_value()
        print(f"  Total Open Pipeline Value: ${total_pipeline:,.2f}")
        print(f"  Total Closed Deals Value: ${closed_value:,.2f}")
        print(f"  Total Leads: {len(self.leads)}")
        print(f"  Total Deals: {len(self.deals)}")
        print()
        
        # Pipeline by Stage
        print(f"{'SALES PIPELINE BY STAGE':-^80}")
        pipeline = self.get_sales_pipeline()
        for stage, deals in pipeline.items():
            if deals:
                total_stage_value = sum(d.amount for d in deals)
                print(f"  {stage.upper()}:")
                print(f"    Count: {len(deals)} deals")
                print(f"    Total Value: ${total_stage_value:,.2f}")
        print()
        
        # Leads Status
        print(f"{'LEADS BY STATUS':-^80}")
        for status in LeadStatus:
            leads = self.get_lead_by_status(status)
            print(f"  {status.value.upper()}: {len(leads)} leads")
        print()
        
        # Sales Rep Performance
        print(f"{'SALES REPRESENTATIVE PERFORMANCE':-^80}")
        for rep_id, rep in self.sales_reps.items():
            performance = self.get_rep_performance(rep_id)
            print(f"  {rep.name} ({rep.region}):")
            print(f"    Deals: {performance['closed_deals']}/{performance['total_deals']} closed")
            print(f"    Win Rate: {performance['win_rate']}")
            print(f"    Closed Value: {performance['closed_deals_value']}")
            print(f"    Quota Attainment: {performance['quota_attainment']}")
            print(f"    Commission Earned: {performance['commission']}")
        print()
        
        # Top Opportunities
        print(f"{'TOP 5 OPEN OPPORTUNITIES':-^80}")
        open_deals = sorted(
            [d for d in self.deals.values() if d.stage != DealStage.CLOSED],
            key=lambda x: x.amount,
            reverse=True
        )[:5]
        for deal in open_deals:
            rep_name = self.sales_reps[deal.assigned_to].name if deal.assigned_to in self.sales_reps else "Unassigned"
            print(f"  • {deal.opportunity_name}")
            print(f"    Amount: ${deal.amount:,.2f} | Stage: {deal.stage.value}")
            print(f"    Assigned to: {rep_name} | Close Date: {deal.expected_close_date.strftime('%Y-%m-%d') if deal.expected_close_date else 'TBD'}")
        print()
        
        # Customer Summary
        print(f"{'CUSTOMER SUMMARY':-^80}")
        print(f"  Total Customers: {len(self.customers)}")
        total_ltv = sum(c.lifetime_value for c in self.customers.values())
        print(f"  Total Customer Lifetime Value: ${total_ltv:,.2f}")
        if self.customers:
            avg_ltv = total_ltv / len(self.customers)
            print(f"  Average Customer Lifetime Value: ${avg_ltv:,.2f}")
        print()
        
        print(f"{'='*80}\n")


def main():
    """Main function demonstrating sales automation"""
    
    # Initialize system
    sales_system = SalesAutomationSystem("TechVision Solutions")
    
    # Add sales representatives
    print("Adding Sales Representatives...\n")
    rep1 = sales_system.add_sales_rep(
        "John Smith", "john.smith@techvision.com", "555-0101",
        "North America", Decimal("0.08"), Decimal("100000")
    )
    rep2 = sales_system.add_sales_rep(
        "Sarah Johnson", "sarah.johnson@techvision.com", "555-0102",
        "Europe", Decimal("0.07"), Decimal("80000")
    )
    print(f"Added {rep1.name} and {rep2.name}\n")
    
    # Add products
    print("Adding Products...\n")
    product1 = sales_system.add_product(
        "CloudSync Pro", SalesProductType.SAAS,
        Decimal("5000"), "Enterprise cloud synchronization", 12
    )
    product2 = sales_system.add_product(
        "DataAnalytics Suite", SalesProductType.SAAS,
        Decimal("3000"), "Advanced data analytics", 12
    )
    product3 = sales_system.add_product(
        "Implementation Services", SalesProductType.CONSULTING,
        Decimal("15000"), "Full implementation support", 1
    )
    print(f"Added {product1.name}, {product2.name}, and {product3.name}\n")
    
    # Create leads
    print("Creating Leads...\n")
    lead1 = sales_system.create_lead(
        "Acme Corporation", "Michael Brown", "mbrown@acme.com",
        "555-1001", "Technology", "High priority prospect"
    )
    lead2 = sales_system.create_lead(
        "Global Enterprises", "Lisa Chen", "lchen@global.com",
        "555-1002", "Finance", "Referred by existing customer"
    )
    lead3 = sales_system.create_lead(
        "Innovation Labs", "David Martinez", "dmartinez@innovlab.com",
        "555-1003", "Healthcare", "Inbound inquiry"
    )
    print(f"Created 3 new leads\n")
    
    # Assign leads to sales reps
    print("Assigning Leads to Sales Representatives...\n")
    sales_system.assign_lead(lead1.lead_id, rep1.rep_id)
    sales_system.assign_lead(lead2.lead_id, rep2.rep_id)
    sales_system.assign_lead(lead3.lead_id, rep1.rep_id)
    print("Leads assigned\n")
    
    # Convert leads to customers and create deals
    print("Converting Leads to Deals...\n")
    customer1 = sales_system.add_customer(
        lead1.company_name, "Technology", "Enterprise",
        lead1.contact_person, lead1.email, lead1.phone, "123 Tech Ave"
    )
    customer2 = sales_system.add_customer(
        lead2.company_name, "Finance", "Large",
        lead2.contact_person, lead2.email, lead2.phone, "456 Finance Blvd"
    )
    
    deal1 = sales_system.create_deal(
        lead1.lead_id, "Acme CloudSync Implementation", 
        "Full implementation of CloudSync Pro for Acme", 
        Decimal("25000"), datetime.now() + timedelta(days=30)
    )
    sales_system.update_lead_status(lead1.lead_id, LeadStatus.PROPOSAL_SENT)
    
    deal2 = sales_system.create_deal(
        lead2.lead_id, "Global Analytics Dashboard",
        "DataAnalytics Suite deployment",
        Decimal("18000"), datetime.now() + timedelta(days=45)
    )
    sales_system.update_lead_status(lead2.lead_id, LeadStatus.PROPOSAL_SENT)
    
    deal3 = sales_system.create_deal(
        lead3.lead_id, "Innovation Labs Digital Transformation",
        "Complete tech stack upgrade",
        Decimal("50000"), datetime.now() + timedelta(days=60)
    )
    
    print(f"Created 3 deals\n")
    
    # Create and send quotes
    print("Creating and Processing Quotes...\n")
    quote1 = sales_system.create_quote(deal1.deal_id, customer1.customer_id)
    sales_system.add_product_to_quote(quote1.quote_id, product1.product_id, 1)
    sales_system.add_product_to_quote(quote1.quote_id, product3.product_id, 1)
    sales_system.send_quote(quote1.quote_id)
    print(f"Quote created for Acme: {quote1}\n")
    
    # Advance deals through pipeline
    print("Advancing Deals Through Pipeline...\n")
    sales_system.advance_deal_stage(deal1.deal_id, DealStage.PROPOSAL)
    sales_system.advance_deal_stage(deal1.deal_id, DealStage.NEGOTIATION)
    sales_system.update_deal_probability(deal1.deal_id, 75)
    
    sales_system.advance_deal_stage(deal2.deal_id, DealStage.PROPOSAL)
    sales_system.update_deal_probability(deal2.deal_id, 60)
    
    # Close a quote and deal
    sales_system.accept_quote(quote1.quote_id)
    sales_system.advance_deal_stage(deal1.deal_id, DealStage.CLOSED)
    print("First deal closed!\n")
    
    # Print comprehensive report
    sales_system.print_sales_report()


if __name__ == "__main__":
    main()
