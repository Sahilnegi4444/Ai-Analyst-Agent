import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_pdf(filename, title, subtitle, sections):
    # Standard margins (54pt = 0.75in)
    doc = SimpleDocTemplate(
        filename, 
        pagesize=letter,
        rightMargin=54, 
        leftMargin=54,
        topMargin=54, 
        bottomMargin=54
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Custom elegant styles using curated HSL-like colors
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1A365D'), # Navy
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#4A5568'), # Slate
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2B6CB0'), # Teal/Blue
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2D3748'), # Charcoal
        spaceAfter=10
    )
    
    # Title & Subtitle
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(subtitle, subtitle_style))
    
    # Elegant divider line
    divider = Table([['']], colWidths=[504])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#1A365D')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0)
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))
    
    # Append Sections
    for sec_title, sec_paras in sections:
        section_story = []
        section_story.append(Paragraph(sec_title, heading_style))
        for para in sec_paras:
            section_story.append(Paragraph(para, body_style))
        section_story.append(Spacer(1, 8))
        story.append(KeepTogether(section_story))
        
    doc.build(story)
    print(f"Generated PDF: {filename}")

def main():
    print("Initializing PDF document generation...")
    # Ensure target folder exists
    os.makedirs('data/documents', exist_ok=True)
    
    # 1. Inventory SOP
    inventory_sop_sections = [
        ("1. Purpose & Scope", [
            "This Standard Operating Procedure (SOP) defines the operational guidelines for managing inventory levels, processing replenishments, and maintaining stock accuracy across all retail warehouses and fulfillment centers.",
            "Maintaining accurate stock logs is critical for customer satisfaction and overall supply chain efficiency. All warehouse team members must strictly follow these protocols."
        ]),
        ("2. Reorder Process & Triggers", [
            "Inventory replenishment must be executed dynamically. The system reviews stock levels daily against the predefined 'Reorder Point' for each SKU.",
            "When stock levels fall to or below the Reorder Point, an automated restock order is generated. The system must order the exact quantity specified as 'Reorder Quantity' for the product to restore safety stock buffer levels.",
            "Emergency purchase orders can only be approved by the Inventory Manager if demand spikes unexpectedly."
        ]),
        ("3. Stock Management & Auditing", [
            "Receiving inbound inventory requires checking packing slips against purchase orders. Any variance in item counts or damage must be documented and submitted to procurement within 24 hours.",
            "Regular cycle counts must be performed weekly. A full warehouse physical inventory audit is conducted semi-annually to reconcile database records with actual physical items and correct accounting books."
        ])
    ]
    create_pdf(
        'data/documents/inventory_sop.pdf',
        'Standard Operating Procedure: Inventory Management',
        'SOP-INV-2025 | Version 1.2 | Operations Department',
        inventory_sop_sections
    )

    # 2. Marketing Policy
    marketing_policy_sections = [
        ("1. Policy Objective", [
            "This corporate policy governs the structure, approval process, and execution rules for all pricing discounts and customer promotional campaigns.",
            "The marketing team must ensure all campaigns support brand integrity, drive sales volumes, and maintain profitability margins."
        ]),
        ("2. Campaign Rules & Setup", [
            "Every promotional campaign must specify start dates, end dates, target product categories, and discount percentages in the marketing database.",
            "Standard campaigns (like the June Summer Savings or December Holiday Extravaganza) must have discount structures pre-tested in staging environments at least 48 hours before launch.",
            "Discounts are limited to a maximum of 25% unless written authorization is obtained from the Chief Marketing Officer."
        ]),
        ("3. Brand Alignment", [
            "All ad copy and graphics must comply with the official brand style manual. Outbound emails must use approved customer segments to maintain high delivery rates and click-through metrics."
        ])
    ]
    create_pdf(
        'data/documents/marketing_policy.pdf',
        'Corporate Marketing & Promotional Campaign Policy',
        'POL-MKT-2025 | Version 2.0 | Corporate Communications',
        marketing_policy_sections
    )

    # 3. Supplier Contract
    supplier_contract_sections = [
        ("1. Scope of Agreement", [
            "This Master Supplier Contract governs all purchase orders and logistics transactions between the Company and its approved suppliers listed in the vendor registry.",
            "The supplier agrees to manufacture and deliver products in accordance with agreed specifications, quality expectations, and packaging requirements."
        ]),
        ("2. SLA Lead Times & Delivery", [
            "Suppliers are required to ship goods within the negotiated Lead Time Days specified in the system registry. The delivery time window starts on the business day following receipt of the Purchase Order.",
            "Failure to meet agreed lead times directly compromises inventory replenishment schedules and fulfillment center operations."
        ]),
        ("3. Penalty & Delay Clauses", [
            "If a supplier fails to deliver products within the designated lead time plus a grace period of 3 business days, the supplier will incur a penalty of 2% of the total purchase order value per delayed day.",
            "Delays exceeding 10 business days will constitute a material breach of contract, allowing the Company to cancel the order and seek damages."
        ])
    ]
    create_pdf(
        'data/documents/supplier_contract.pdf',
        'Standard Vendor & Supplier Service Level Agreement',
        'CON-SUP-TEMPLATE | Procurement & Logistics',
        supplier_contract_sections
    )

    # 4. Monthly Executive Report (March)
    executive_report_sections = [
        ("1. Executive Summary", [
            "This report summarizes retail operations and performance metrics for the month of March 2025. Total revenue was moderately impacted due to severe supply chain bottlenecks and localized stockouts."
        ]),
        ("2. Sales & Revenue Summary", [
            "Overall monthly sales volumes were lower than the seasonal projections. Although categories like Apparel and Home & Kitchen performed steadily, the Electronics category experienced a sharp decline in sales volume."
        ]),
        ("3. Critical Supply Chain Event: Product A Shortage", [
            "On March 5, 2025, Warehouse A experienced a major operations stoppage (registered as 'Warehouse A Delay') due to automated sorting system failures. This halted the receipt of all inbound electronics shipments.",
            "As a direct consequence, the inventory level of Product A (P001) fell to 0. The stockout persisted throughout March 2025, as shown in the weekly inventory log ('Out of Stock' status).",
            "This supply chain gap led to zero sales records for Product A in the month of March, resulting in an estimated sales loss of approximately $15,000. Normal inventory flow was successfully restored in April 2025."
        ])
    ]
    create_pdf(
        'data/documents/monthly_executive_report_march.pdf',
        'Monthly Executive Business Performance Report: March 2025',
        'REP-EXEC-2025-M03 | Confidential | Executive Board',
        executive_report_sections
    )

    # 5. Warehouse Manual
    warehouse_manual_sections = [
        ("1. Warehouse Operations Overview", [
            "This manual specifies the operational workflows and safety regulations for inbound logistics, inventory sorting, item picking, packing, and shipping across our network."
        ]),
        ("2. Shipping & Dispatch Procedures", [
            "Orders must be picked using automated picking lists. Item barcodes must be scanned at the dispatch station to update database levels immediately.",
            "Fulfillment packers must use standardized cartons and eco-friendly packing paper. All outbound boxes must be sealed and placed on carrier pallets by 4:00 PM local time to meet carrier SLA departure windows."
        ]),
        ("3. Carrier Coordination", [
            "Any delay in carrier handoffs or shipping congestions must be logged in the system to enable dynamic shipping estimation updates on the customer storefront."
        ])
    ]
    create_pdf(
        'data/documents/warehouse_manual.pdf',
        'Warehouse Operations and Shipping Procedures Manual',
        'MAN-OPS-2025 | Logistics & Fulfillment Team',
        warehouse_manual_sections
    )
    print("Successfully generated all business PDFs in data/documents/")

if __name__ == '__main__':
    main()
