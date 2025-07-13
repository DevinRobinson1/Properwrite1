"""
Seed Construction Catalog Database
Populates the construction_catalog table with sample data based on Excel workbooks
"""

import sqlite3
import logging
from construction_models import construction_db

def seed_fix_flip_catalog():
    """Seed Fix & Flip catalog based on Renovo Full Renovation Estimator"""
    fix_flip_items = [
        # EXTERIOR DETAIL
        ('Roofing', 'Roof Replacement', 'SQ', 18, 46.00, 5.11, 'Tear off existing, reshingle'),
        ('Roofing', 'Roof Resheeting', 'SQ', 18, 30.00, 25.00, 'Plywood replacement'),
        ('Siding', 'Siding Replacement', 'SQ', 17, 63.16, 159.41, 'Vinyl siding replacement'),
        ('Gutters', 'Gutter Replacement', 'LF', 144, 15.63, 3.13, 'Seamless aluminum gutters'),
        ('Foundation', 'Foundation Repair', 'LF', 15, 80.00, 128.00, 'Foundation straightening/rebuild'),
        ('Painting', 'Exterior Painting', 'SQ', 15, 0.00, 0.00, 'Exterior paint job'),
        ('Windows', 'Window Replacement', 'EA', 8, 350.00, 450.00, 'Standard vinyl windows'),
        ('Doors', 'Exterior Door', 'EA', 2, 400.00, 600.00, 'Entry door with hardware'),
        ('Porch', 'Porch Decking', 'SF', 75, 15.00, 8.00, 'Composite decking'),
        ('Landscaping', 'Tree Trimming', 'EA', 4, 150.00, 0.00, 'Professional tree service'),
        ('Landscaping', 'Tree Removal', 'EA', 0, 500.00, 0.00, 'Complete tree removal'),
        ('Landscaping', 'Yard Cleanup', 'LS', 1, 800.00, 350.00, 'General yard cleanup'),
        
        # MECHANICAL DETAIL
        ('HVAC', 'New Gas Meter Install', 'EA', 1, 400.00, 200.00, 'Gas meter installation'),
        ('HVAC', 'New Furnace Install', 'EA', 1, 2000.00, 2500.00, 'Central heating system'),
        ('HVAC', 'Furnace Replacement', 'EA', 1, 1500.00, 2000.00, 'Replace existing furnace'),
        ('HVAC', 'New AC Install', 'EA', 1, 1500.00, 2000.00, 'Central air conditioning'),
        ('HVAC', 'AC Replacement', 'EA', 0, 1200.00, 1800.00, 'Replace existing AC unit'),
        ('HVAC', 'Bath Fan Install', 'EA', 2, 150.00, 100.00, 'Bathroom exhaust fan'),
        ('HVAC', 'Ductwork', 'LS', 1, 1500.00, 800.00, 'Complete ductwork system'),
        
        ('Electrical', 'Vanity Light Replacement', 'EA', 2, 75.00, 125.00, 'Bathroom vanity lighting'),
        ('Electrical', 'Flush Light Replacement', 'EA', 8, 50.00, 75.00, 'Ceiling flush mount lights'),
        ('Electrical', 'Wall Sconce Replacement', 'EA', 0, 100.00, 150.00, 'Wall mounted lighting'),
        ('Electrical', 'Flood Light Replacement', 'EA', 2, 80.00, 120.00, 'Exterior flood lights'),
        ('Electrical', 'Ceiling Fan Replacement', 'EA', 3, 120.00, 180.00, 'Ceiling fan with light'),
        ('Electrical', 'Closet Light Replacement', 'EA', 4, 40.00, 60.00, 'Closet lighting'),
        ('Electrical', 'Smoke Detector Install', 'EA', 6, 25.00, 35.00, 'Hardwired smoke detector'),
        ('Electrical', 'CO Detector Install', 'EA', 3, 30.00, 45.00, 'Carbon monoxide detector'),
        ('Electrical', 'New Electric Panel', 'EA', 1, 800.00, 1200.00, '200 amp electrical panel'),
        ('Electrical', 'New Electric Meter', 'EA', 1, 400.00, 300.00, 'Electric meter installation'),
        ('Electrical', 'Rewire House', 'LS', 1, 3000.00, 2500.00, 'Complete house rewiring'),
        
        ('Plumbing', 'New Water Meter Install', 'EA', 1, 300.00, 200.00, 'Water meter installation'),
        ('Plumbing', 'New Gas Water Heater', 'EA', 1, 400.00, 600.00, '40 gallon gas water heater'),
        ('Plumbing', 'Replace Gas Water Heater', 'EA', 0, 350.00, 500.00, 'Replace existing gas WH'),
        ('Plumbing', 'New Electric Water Heater', 'EA', 0, 300.00, 500.00, '40 gallon electric WH'),
        ('Plumbing', 'Replace Electric Water Heater', 'EA', 0, 250.00, 400.00, 'Replace existing electric WH'),
        ('Plumbing', 'New Sink Location', 'EA', 0, 400.00, 300.00, 'Plumbing for new sink'),
        ('Plumbing', 'New Toilet Location', 'EA', 0, 500.00, 200.00, 'Plumbing for new toilet'),
        ('Plumbing', 'New Tub/Shower Location', 'EA', 0, 800.00, 400.00, 'Plumbing for tub/shower'),
        ('Plumbing', 'Repipe House', 'LS', 1, 2000.00, 1500.00, 'Complete house repiping'),
        
        # INTERIOR DETAIL
        ('Kitchen', 'Kitchen Renovation', 'SF', 230, 8.61, 19.60, 'Complete kitchen renovation'),
        ('Kitchen', 'Countertop Installation', 'LF', 30, 40.00, 60.00, 'Laminate countertops'),
        ('Kitchen', 'New Gas Stove', 'EA', 1, 100.00, 800.00, 'Gas range installation'),
        ('Kitchen', 'New Electric Stove', 'EA', 0, 100.00, 700.00, 'Electric range installation'),
        ('Kitchen', 'New Dishwasher', 'EA', 1, 150.00, 600.00, 'Built-in dishwasher'),
        ('Kitchen', 'New Refrigerator', 'EA', 0, 0.00, 1200.00, 'Standard refrigerator'),
        ('Kitchen', 'New Microwave', 'EA', 0, 50.00, 300.00, 'Over-range microwave'),
        ('Kitchen', 'New Garbage Disposal', 'EA', 1, 100.00, 150.00, 'Garbage disposal unit'),
        ('Kitchen', 'New Washing Machine', 'EA', 0, 100.00, 800.00, 'Washing machine hookup'),
        ('Kitchen', 'New Dryer', 'EA', 0, 100.00, 700.00, 'Dryer hookup'),
        
        ('Flooring', 'Hardwood Flooring', 'SF', 1000, 3.00, 8.00, 'Engineered hardwood'),
        ('Flooring', 'Tile Flooring', 'SF', 400, 4.00, 6.00, 'Ceramic tile installation'),
        ('Flooring', 'Carpet Installation', 'SF', 600, 2.00, 4.00, 'Standard carpet with pad'),
        ('Flooring', 'Vinyl Plank Flooring', 'SF', 800, 2.50, 5.00, 'Luxury vinyl plank'),
        ('Flooring', 'Subfloor Replacement', 'SF', 200, 3.00, 2.00, 'Plywood subfloor'),
        
        ('Bathroom', 'Bathroom Renovation', 'SF', 50, 25.00, 35.00, 'Complete bathroom renovation'),
        ('Bathroom', 'New Toilet', 'EA', 3, 150.00, 300.00, 'Standard toilet installation'),
        ('Bathroom', 'New Vanity', 'EA', 2, 200.00, 500.00, 'Bathroom vanity with top'),
        ('Bathroom', 'New Bathtub', 'EA', 1, 400.00, 800.00, 'Standard bathtub'),
        ('Bathroom', 'New Shower', 'EA', 1, 600.00, 1200.00, 'Tile shower installation'),
        ('Bathroom', 'Bathroom Tile', 'SF', 100, 8.00, 12.00, 'Ceramic wall and floor tile'),
        
        ('Drywall', 'Drywall Installation', 'SF', 2000, 1.50, 0.75, 'Drywall hanging and finishing'),
        ('Drywall', 'Drywall Repair', 'SF', 200, 2.00, 1.00, 'Patch and repair drywall'),
        ('Drywall', 'Texture Application', 'SF', 2000, 0.50, 0.25, 'Orange peel texture'),
        
        ('Painting', 'Interior Painting', 'SF', 2000, 1.50, 0.75, 'Prime and paint interior'),
        ('Painting', 'Exterior Painting', 'SF', 1500, 2.00, 1.00, 'Prime and paint exterior'),
        ('Painting', 'Trim Painting', 'LF', 500, 1.00, 0.50, 'Prime and paint trim'),
        
        ('Doors', 'Interior Door', 'EA', 8, 150.00, 200.00, 'Standard interior door'),
        ('Doors', 'Door Hardware', 'EA', 10, 25.00, 75.00, 'Door knobs and hinges'),
        
        ('Trim', 'Baseboard Installation', 'LF', 400, 2.00, 3.00, 'Standard baseboard trim'),
        ('Trim', 'Crown Molding', 'LF', 200, 4.00, 6.00, 'Crown molding installation'),
        ('Trim', 'Window Trim', 'LF', 160, 3.00, 4.00, 'Window casing trim'),
        
        ('Insulation', 'Wall Insulation', 'SF', 1500, 0.75, 1.25, 'Batt insulation R-13'),
        ('Insulation', 'Attic Insulation', 'SF', 1000, 0.50, 1.00, 'Blown-in insulation R-30'),
        
        ('Permits', 'Building Permit', 'LS', 1, 0.00, 500.00, 'General building permit'),
        ('Permits', 'Electrical Permit', 'LS', 1, 0.00, 150.00, 'Electrical work permit'),
        ('Permits', 'Plumbing Permit', 'LS', 1, 0.00, 100.00, 'Plumbing work permit'),
        ('Permits', 'HVAC Permit', 'LS', 1, 0.00, 125.00, 'HVAC work permit'),
        
        ('Cleanup', 'Construction Cleanup', 'LS', 1, 800.00, 300.00, 'Final construction cleanup'),
        ('Cleanup', 'Dumpster Rental', 'LS', 2, 0.00, 400.00, '30-yard dumpster rental'),
    ]
    
    try:
        conn = sqlite3.connect(construction_db.db_path)
        cursor = conn.cursor()
        
        for item in fix_flip_items:
            cursor.execute('''
                INSERT INTO construction_catalog 
                (trade, sub_item, unit, default_qty, labor_cost, material_cost, notes, project_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*item, 'fix_flip'))
        
        conn.commit()
        conn.close()
        logging.info(f"Seeded {len(fix_flip_items)} Fix & Flip catalog items")
        
    except Exception as e:
        logging.error(f"Error seeding Fix & Flip catalog: {e}")

def seed_new_construction_catalog():
    """Seed New Construction catalog based on Template - New Construction Breakdown"""
    new_construction_items = [
        # FOUNDATION & SITE WORK
        ('Site Work', 'Site Survey', 'LS', 1, 0.00, 800.00, 'Professional site survey'),
        ('Site Work', 'Site Preparation', 'LS', 1, 2000.00, 500.00, 'Clearing and grading'),
        ('Site Work', 'Excavation', 'CY', 200, 8.00, 0.00, 'Foundation excavation'),
        ('Site Work', 'Utility Connections', 'LS', 1, 1500.00, 2000.00, 'Water, sewer, electric connections'),
        ('Site Work', 'Driveway', 'SF', 600, 2.00, 4.00, 'Concrete driveway'),
        ('Site Work', 'Sidewalk', 'SF', 200, 3.00, 5.00, 'Concrete sidewalk'),
        
        ('Foundation', 'Foundation Footings', 'LF', 160, 8.00, 12.00, 'Concrete footings'),
        ('Foundation', 'Foundation Walls', 'LF', 160, 15.00, 20.00, 'Concrete block walls'),
        ('Foundation', 'Foundation Slab', 'SF', 1500, 3.00, 4.00, 'Concrete slab on grade'),
        ('Foundation', 'Basement Excavation', 'CY', 0, 10.00, 0.00, 'Basement excavation'),
        ('Foundation', 'Basement Walls', 'SF', 0, 8.00, 12.00, 'Poured concrete walls'),
        ('Foundation', 'Basement Slab', 'SF', 0, 4.00, 5.00, 'Basement floor slab'),
        ('Foundation', 'Waterproofing', 'SF', 0, 2.00, 3.00, 'Foundation waterproofing'),
        
        # FRAMING & STRUCTURE
        ('Framing', 'Floor Framing', 'SF', 1500, 4.00, 6.00, 'Floor joists and subflooring'),
        ('Framing', 'Wall Framing', 'SF', 3000, 3.00, 4.00, 'Exterior and interior walls'),
        ('Framing', 'Roof Framing', 'SF', 1500, 5.00, 7.00, 'Roof trusses and decking'),
        ('Framing', 'Stairs', 'LS', 1, 800.00, 1200.00, 'Interior staircase'),
        ('Framing', 'Porch Framing', 'SF', 200, 6.00, 8.00, 'Covered porch framing'),
        
        # ROOFING & EXTERIOR
        ('Roofing', 'Roof Shingles', 'SQ', 16, 80.00, 120.00, 'Architectural shingles'),
        ('Roofing', 'Gutters', 'LF', 120, 6.00, 8.00, 'Seamless aluminum gutters'),
        ('Roofing', 'Flashing', 'LF', 80, 3.00, 4.00, 'Roof flashing'),
        ('Roofing', 'Ventilation', 'EA', 4, 50.00, 75.00, 'Roof vents'),
        
        ('Siding', 'House Siding', 'SQ', 20, 120.00, 180.00, 'Fiber cement siding'),
        ('Siding', 'Trim Work', 'LF', 400, 4.00, 6.00, 'Exterior trim boards'),
        ('Siding', 'Soffit and Fascia', 'LF', 120, 8.00, 10.00, 'Aluminum soffit and fascia'),
        
        ('Windows', 'Windows', 'EA', 12, 200.00, 600.00, 'Vinyl double-hung windows'),
        ('Windows', 'Sliding Glass Door', 'EA', 1, 300.00, 800.00, 'Patio sliding door'),
        ('Doors', 'Front Door', 'EA', 1, 200.00, 800.00, 'Solid wood front door'),
        ('Doors', 'Back Door', 'EA', 1, 150.00, 400.00, 'Steel back door'),
        ('Doors', 'Garage Door', 'EA', 2, 300.00, 600.00, 'Insulated garage door'),
        
        # MECHANICAL SYSTEMS
        ('HVAC', 'HVAC System', 'LS', 1, 4000.00, 6000.00, 'Complete HVAC system'),
        ('HVAC', 'Ductwork', 'LS', 1, 2000.00, 1500.00, 'Complete ductwork system'),
        ('HVAC', 'Air Conditioning', 'TON', 3, 800.00, 1200.00, 'Central air conditioning'),
        ('HVAC', 'Furnace', 'LS', 1, 1000.00, 2000.00, 'Gas furnace'),
        ('HVAC', 'Thermostats', 'EA', 2, 100.00, 200.00, 'Programmable thermostats'),
        
        ('Plumbing', 'Rough Plumbing', 'LS', 1, 3000.00, 2000.00, 'Rough plumbing installation'),
        ('Plumbing', 'Plumbing Fixtures', 'LS', 1, 2000.00, 3000.00, 'All plumbing fixtures'),
        ('Plumbing', 'Water Heater', 'EA', 1, 400.00, 800.00, 'Gas water heater'),
        ('Plumbing', 'Septic System', 'LS', 0, 2000.00, 3000.00, 'Septic tank and field'),
        ('Plumbing', 'Well', 'LS', 0, 1000.00, 4000.00, 'Water well installation'),
        
        ('Electrical', 'Rough Electrical', 'LS', 1, 3500.00, 2500.00, 'Rough electrical installation'),
        ('Electrical', 'Electrical Panel', 'EA', 1, 600.00, 800.00, '200 amp electrical panel'),
        ('Electrical', 'Light Fixtures', 'LS', 1, 800.00, 1200.00, 'All interior light fixtures'),
        ('Electrical', 'Outlets and Switches', 'LS', 1, 600.00, 400.00, 'All outlets and switches'),
        ('Electrical', 'Ceiling Fans', 'EA', 4, 100.00, 200.00, 'Ceiling fans with lights'),
        
        # INSULATION & DRYWALL
        ('Insulation', 'Wall Insulation', 'SF', 3000, 1.00, 1.50, 'Fiberglass batt insulation'),
        ('Insulation', 'Attic Insulation', 'SF', 1500, 0.75, 1.25, 'Blown-in insulation'),
        ('Insulation', 'Basement Insulation', 'SF', 0, 1.25, 1.75, 'Rigid foam insulation'),
        
        ('Drywall', 'Drywall Installation', 'SF', 4000, 1.50, 0.75, 'Drywall hanging and finishing'),
        ('Drywall', 'Texture', 'SF', 4000, 0.50, 0.25, 'Wall texture application'),
        
        # INTERIOR FINISHES
        ('Flooring', 'Hardwood Flooring', 'SF', 1200, 5.00, 8.00, 'Solid hardwood flooring'),
        ('Flooring', 'Tile Flooring', 'SF', 400, 6.00, 8.00, 'Ceramic tile installation'),
        ('Flooring', 'Carpet', 'SF', 800, 3.00, 4.00, 'Carpet with pad'),
        ('Flooring', 'Vinyl Flooring', 'SF', 200, 4.00, 6.00, 'Luxury vinyl plank'),
        
        ('Kitchen', 'Kitchen Cabinets', 'LF', 25, 200.00, 800.00, 'Custom kitchen cabinets'),
        ('Kitchen', 'Countertops', 'SF', 40, 40.00, 60.00, 'Granite countertops'),
        ('Kitchen', 'Kitchen Appliances', 'LS', 1, 500.00, 4000.00, 'Full appliance package'),
        ('Kitchen', 'Kitchen Backsplash', 'SF', 30, 8.00, 12.00, 'Tile backsplash'),
        
        ('Bathroom', 'Bathroom Vanities', 'EA', 3, 300.00, 800.00, 'Bathroom vanity with top'),
        ('Bathroom', 'Bathroom Fixtures', 'LS', 1, 800.00, 1200.00, 'Toilets, tubs, showers'),
        ('Bathroom', 'Bathroom Tile', 'SF', 300, 8.00, 12.00, 'Ceramic wall and floor tile'),
        
        ('Doors', 'Interior Doors', 'EA', 12, 150.00, 300.00, 'Interior doors with hardware'),
        ('Doors', 'Closet Doors', 'EA', 8, 100.00, 200.00, 'Bifold closet doors'),
        
        ('Trim', 'Baseboard', 'LF', 600, 3.00, 4.00, 'Baseboard trim'),
        ('Trim', 'Crown Molding', 'LF', 400, 5.00, 6.00, 'Crown molding'),
        ('Trim', 'Window Trim', 'LF', 240, 4.00, 5.00, 'Window casing'),
        ('Trim', 'Door Trim', 'LF', 180, 3.00, 4.00, 'Door casing'),
        
        ('Painting', 'Interior Painting', 'SF', 4000, 1.50, 0.75, 'Prime and paint interior'),
        ('Painting', 'Exterior Painting', 'SF', 2000, 2.00, 1.00, 'Prime and paint exterior'),
        
        # PERMITS & FINAL
        ('Permits', 'Building Permit', 'LS', 1, 0.00, 1500.00, 'New construction permit'),
        ('Permits', 'Impact Fees', 'LS', 1, 0.00, 3000.00, 'City impact fees'),
        ('Permits', 'Inspections', 'LS', 1, 0.00, 500.00, 'Required inspections'),
        
        ('Cleanup', 'Final Cleanup', 'LS', 1, 1000.00, 500.00, 'Final construction cleanup'),
        ('Cleanup', 'Landscaping', 'LS', 1, 2000.00, 1500.00, 'Basic landscaping'),
        ('Cleanup', 'Driveway Sealing', 'SF', 600, 0.50, 0.75, 'Concrete sealing'),
    ]
    
    try:
        conn = sqlite3.connect(construction_db.db_path)
        cursor = conn.cursor()
        
        for item in new_construction_items:
            cursor.execute('''
                INSERT INTO construction_catalog 
                (trade, sub_item, unit, default_qty, labor_cost, material_cost, notes, project_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*item, 'new_construction'))
        
        conn.commit()
        conn.close()
        logging.info(f"Seeded {len(new_construction_items)} New Construction catalog items")
        
    except Exception as e:
        logging.error(f"Error seeding New Construction catalog: {e}")

def seed_all_construction_data():
    """Seed all construction catalog data"""
    try:
        logging.info("Starting construction catalog seeding...")
        seed_fix_flip_catalog()
        seed_new_construction_catalog()
        logging.info("Construction catalog seeding completed successfully")
        
    except Exception as e:
        logging.error(f"Error seeding construction catalog: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_all_construction_data()