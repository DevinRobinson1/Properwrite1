"""
Construction Database Models and Operations
Handles construction catalog data for Fix & Flip and New Construction estimators
"""

import sqlite3
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

class ConstructionDatabase:
    def __init__(self, db_path: str = "construction.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize construction database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create construction_catalog table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS construction_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade TEXT NOT NULL,
                    sub_item TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    default_qty REAL DEFAULT 1.0,
                    labor_cost REAL DEFAULT 0.0,
                    material_cost REAL DEFAULT 0.0,
                    notes TEXT,
                    project_type TEXT NOT NULL CHECK (project_type IN ('fix_flip', 'new_construction')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create construction_projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS construction_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    project_name TEXT NOT NULL,
                    project_type TEXT NOT NULL CHECK (project_type IN ('fix_flip', 'new_construction')),
                    property_address TEXT,
                    property_sqft REAL,
                    hard_costs REAL DEFAULT 0.0,
                    overhead_percent REAL DEFAULT 0.0,
                    contingency_percent REAL DEFAULT 0.0,
                    gc_fee_percent REAL DEFAULT 0.0,
                    land_cost REAL DEFAULT 0.0,
                    carry_cost REAL DEFAULT 0.0,
                    total_budget REAL DEFAULT 0.0,
                    project_data TEXT,  -- JSON string for storing line items
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create construction_line_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS construction_line_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    trade TEXT NOT NULL,
                    sub_item TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    labor_cost REAL NOT NULL,
                    material_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES construction_projects (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Construction database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing construction database: {e}")
            raise
    
    def get_catalog_items(self, project_type: str, trade: str = None) -> List[Dict]:
        """Get catalog items filtered by project type and optionally by trade"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if trade:
                cursor.execute('''
                    SELECT id, trade, sub_item, unit, default_qty, labor_cost, material_cost, notes
                    FROM construction_catalog 
                    WHERE project_type = ? AND trade = ?
                    ORDER BY trade, sub_item
                ''', (project_type, trade))
            else:
                cursor.execute('''
                    SELECT id, trade, sub_item, unit, default_qty, labor_cost, material_cost, notes
                    FROM construction_catalog 
                    WHERE project_type = ?
                    ORDER BY trade, sub_item
                ''', (project_type,))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'id': row[0],
                    'trade': row[1],
                    'sub_item': row[2],
                    'unit': row[3],
                    'default_qty': row[4],
                    'labor_cost': row[5],
                    'material_cost': row[6],
                    'notes': row[7] or ''
                })
            
            conn.close()
            return items
            
        except Exception as e:
            logging.error(f"Error getting catalog items: {e}")
            return []
    
    def get_trades(self, project_type: str) -> List[str]:
        """Get all trade categories for a project type"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT trade FROM construction_catalog 
                WHERE project_type = ?
                ORDER BY trade
            ''', (project_type,))
            
            trades = [row[0] for row in cursor.fetchall()]
            conn.close()
            return trades
            
        except Exception as e:
            logging.error(f"Error getting trades: {e}")
            return []
    
    def create_project(self, user_id: int, project_name: str, project_type: str, 
                      property_address: str = None, property_sqft: float = None) -> int:
        """Create a new construction project"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO construction_projects 
                (user_id, project_name, project_type, property_address, property_sqft)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, project_name, project_type, property_address, property_sqft))
            
            project_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return project_id
            
        except Exception as e:
            logging.error(f"Error creating project: {e}")
            return None
    
    def save_project_budget(self, project_id: int, budget_data: Dict) -> bool:
        """Save project budget data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE construction_projects 
                SET hard_costs = ?, overhead_percent = ?, contingency_percent = ?, 
                    gc_fee_percent = ?, land_cost = ?, carry_cost = ?, total_budget = ?,
                    project_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                budget_data.get('hard_costs', 0),
                budget_data.get('overhead_percent', 0),
                budget_data.get('contingency_percent', 0),
                budget_data.get('gc_fee_percent', 0),
                budget_data.get('land_cost', 0),
                budget_data.get('carry_cost', 0),
                budget_data.get('total_budget', 0),
                json.dumps(budget_data),
                project_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logging.error(f"Error saving project budget: {e}")
            return False
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get project details by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM construction_projects WHERE id = ?
            ''', (project_id,))
            
            row = cursor.fetchone()
            if row:
                project = {
                    'id': row[0],
                    'user_id': row[1],
                    'project_name': row[2],
                    'project_type': row[3],
                    'property_address': row[4],
                    'property_sqft': row[5],
                    'hard_costs': row[6],
                    'overhead_percent': row[7],
                    'contingency_percent': row[8],
                    'gc_fee_percent': row[9],
                    'land_cost': row[10],
                    'carry_cost': row[11],
                    'total_budget': row[12],
                    'project_data': json.loads(row[13]) if row[13] else {},
                    'created_at': row[14],
                    'updated_at': row[15]
                }
                conn.close()
                return project
            
            conn.close()
            return None
            
        except Exception as e:
            logging.error(f"Error getting project: {e}")
            return None

# Global instance
construction_db = ConstructionDatabase()