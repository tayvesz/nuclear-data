"""
Build Complete Dataset - Full Data Ingestion Pipeline

Downloads and processes:
1. GeoNuclearData (804 reactors worldwide)
2. Simulated maintenance records based on real reactor data
3. Simulated incidents with realistic distributions
4. NRC public documents for RAG

Sources:
- https://github.com/cristianst85/GeoNuclearData
- https://www.nrc.gov/reading-rm/doc-collections/
"""

import pandas as pd
import requests
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import json
import os


# GeoNuclearData URLs (try multiple formats)
GEONUCLEAR_URLS = [
    "https://raw.githubusercontent.com/cristianst85/GeoNuclearData/master/data/json/reactors.json",
    "https://raw.githubusercontent.com/cristianst85/GeoNuclearData/main/data/json/reactors.json",
]

# NRC Public Documents for RAG
NRC_DOCUMENTS = [
    {
        "url": "https://www.nrc.gov/docs/ML2220/ML22207A388.pdf",
        "name": "NRC_Inspection_Report_Framatome_2022.pdf",
        "doc_type": "inspection"
    },
    {
        "url": "https://www.nrc.gov/docs/ML2321/ML23214A221.pdf",
        "name": "NRC_Safety_Evaluation_2023.pdf",
        "doc_type": "safety"
    },
]

# Equipment types with realistic MTBF/MTTR
EQUIPMENT_CATALOG = [
    {"name": "Primary Coolant Pump", "category": "mécanique", "mtbf_hours": 8760, "mttr_hours": 48, "criticality": "high"},
    {"name": "Control Valve", "category": "mécanique", "mtbf_hours": 4380, "mttr_hours": 8, "criticality": "medium"},
    {"name": "Temperature Sensor PT100", "category": "instrumentation", "mtbf_hours": 17520, "mttr_hours": 4, "criticality": "low"},
    {"name": "Pressure Transmitter", "category": "instrumentation", "mtbf_hours": 17520, "mttr_hours": 6, "criticality": "medium"},
    {"name": "Emergency Diesel Generator", "category": "électrique", "mtbf_hours": 2190, "mttr_hours": 72, "criticality": "high"},
    {"name": "Main Transformer", "category": "électrique", "mtbf_hours": 43800, "mttr_hours": 168, "criticality": "high"},
    {"name": "Steam Generator", "category": "thermique", "mtbf_hours": 26280, "mttr_hours": 240, "criticality": "high"},
    {"name": "Main Turbine", "category": "mécanique", "mtbf_hours": 8760, "mttr_hours": 120, "criticality": "high"},
    {"name": "Feedwater Pump", "category": "mécanique", "mtbf_hours": 6570, "mttr_hours": 24, "criticality": "medium"},
    {"name": "Motor-Operated Valve", "category": "électrique", "mtbf_hours": 8760, "mttr_hours": 12, "criticality": "medium"},
    {"name": "Reactor Protection System", "category": "instrumentation", "mtbf_hours": 87600, "mttr_hours": 8, "criticality": "high"},
    {"name": "Containment Isolation Valve", "category": "mécanique", "mtbf_hours": 43800, "mttr_hours": 24, "criticality": "high"},
    {"name": "Cooling Tower Fan", "category": "mécanique", "mtbf_hours": 4380, "mttr_hours": 16, "criticality": "low"},
    {"name": "Neutron Flux Detector", "category": "instrumentation", "mtbf_hours": 26280, "mttr_hours": 12, "criticality": "high"},
    {"name": "Boric Acid Pump", "category": "mécanique", "mtbf_hours": 8760, "mttr_hours": 18, "criticality": "medium"},
]


def download_geonuclear_data() -> pd.DataFrame:
    """
    Download reactor data from GeoNuclearData GitHub repository.
    Falls back to local French reactor data if download fails.
    """
    print("📥 Downloading GeoNuclearData...")
    
    for url in GEONUCLEAR_URLS:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                print(f"  ✓ Downloaded {len(df)} reactors from GeoNuclearData")
                return df
        except Exception as e:
            print(f"  ⚠ Failed to download from {url}: {e}")
    
    print("  ℹ Using local French reactor data as fallback")
    return create_french_reactor_data()


def create_french_reactor_data() -> pd.DataFrame:
    """
    Create comprehensive French nuclear fleet data.
    Based on real EDF/Framatome reactor specifications.
    """
    reactors = [
        # 900 MW Series (CP0, CP1, CP2)
        {"name": "Fessenheim-1", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Shutdown", "country": "France",
         "thermal_capacity": 2660, "gross_capacity": 920, "operational_from": "1977-04-06", "operational_to": "2020-02-22"},
        {"name": "Fessenheim-2", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Shutdown", "country": "France",
         "thermal_capacity": 2660, "gross_capacity": 920, "operational_from": "1977-10-18", "operational_to": "2020-06-30"},
        {"name": "Bugey-2", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 945, "operational_from": "1978-05-10", "operational_to": None},
        {"name": "Bugey-3", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 945, "operational_from": "1978-09-21", "operational_to": None},
        {"name": "Bugey-4", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 917, "operational_from": "1979-03-08", "operational_to": None},
        {"name": "Bugey-5", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 917, "operational_from": "1979-07-31", "operational_to": None},
        
        # CP1 Series
        {"name": "Tricastin-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 955, "operational_from": "1980-05-31", "operational_to": None},
        {"name": "Tricastin-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 955, "operational_from": "1980-08-01", "operational_to": None},
        {"name": "Tricastin-3", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 955, "operational_from": "1981-02-10", "operational_to": None},
        {"name": "Tricastin-4", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 955, "operational_from": "1981-06-01", "operational_to": None},
        {"name": "Gravelines-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1980-03-13", "operational_to": None},
        {"name": "Gravelines-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1980-08-26", "operational_to": None},
        {"name": "Gravelines-3", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1980-12-12", "operational_to": None},
        {"name": "Gravelines-4", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1981-06-14", "operational_to": None},
        {"name": "Gravelines-5", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1984-08-28", "operational_to": None},
        {"name": "Gravelines-6", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1985-08-01", "operational_to": None},
        {"name": "Dampierre-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 937, "operational_from": "1980-03-23", "operational_to": None},
        {"name": "Dampierre-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 937, "operational_from": "1980-12-10", "operational_to": None},
        {"name": "Dampierre-3", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 937, "operational_from": "1981-01-30", "operational_to": None},
        {"name": "Dampierre-4", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 937, "operational_from": "1981-08-18", "operational_to": None},
        {"name": "Blayais-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1981-06-12", "operational_to": None},
        {"name": "Blayais-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1982-07-17", "operational_to": None},
        {"name": "Blayais-3", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1983-08-17", "operational_to": None},
        {"name": "Blayais-4", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 951, "operational_from": "1983-05-16", "operational_to": None},
        
        # CP2 Series
        {"name": "Chinon-B1", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 954, "operational_from": "1982-11-30", "operational_to": None},
        {"name": "Chinon-B2", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 954, "operational_from": "1983-11-29", "operational_to": None},
        {"name": "Chinon-B3", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 954, "operational_from": "1986-10-20", "operational_to": None},
        {"name": "Chinon-B4", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 954, "operational_from": "1987-11-14", "operational_to": None},
        {"name": "Cruas-1", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1983-04-29", "operational_to": None},
        {"name": "Cruas-2", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1984-09-06", "operational_to": None},
        {"name": "Cruas-3", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1984-05-14", "operational_to": None},
        {"name": "Cruas-4", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1984-10-27", "operational_to": None},
        {"name": "Saint-Laurent-B1", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1981-08-21", "operational_to": None},
        {"name": "Saint-Laurent-B2", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 2785, "gross_capacity": 956, "operational_from": "1981-08-01", "operational_to": None},
        
        # 1300 MW Series (P4, P'4)
        {"name": "Paluel-1", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1984-06-22", "operational_to": None},
        {"name": "Paluel-2", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1984-09-14", "operational_to": None},
        {"name": "Paluel-3", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1985-09-30", "operational_to": None},
        {"name": "Paluel-4", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1986-04-11", "operational_to": None},
        {"name": "Flamanville-1", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1985-12-04", "operational_to": None},
        {"name": "Flamanville-2", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1986-07-18", "operational_to": None},
        {"name": "Saint-Alban-1", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1381, "operational_from": "1985-08-30", "operational_to": None},
        {"name": "Saint-Alban-2", "reactor_model": "P4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1381, "operational_from": "1986-07-03", "operational_to": None},
        {"name": "Cattenom-1", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1362, "operational_from": "1986-11-13", "operational_to": None},
        {"name": "Cattenom-2", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1362, "operational_from": "1987-09-17", "operational_to": None},
        {"name": "Cattenom-3", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1362, "operational_from": "1990-07-06", "operational_to": None},
        {"name": "Cattenom-4", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1362, "operational_from": "1991-05-27", "operational_to": None},
        {"name": "Belleville-1", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1987-10-14", "operational_to": None},
        {"name": "Belleville-2", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1988-07-06", "operational_to": None},
        {"name": "Nogent-1", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1987-10-21", "operational_to": None},
        {"name": "Nogent-2", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1988-12-14", "operational_to": None},
        {"name": "Penly-1", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1990-05-04", "operational_to": None},
        {"name": "Penly-2", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1382, "operational_from": "1992-02-04", "operational_to": None},
        {"name": "Golfech-1", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1990-06-07", "operational_to": None},
        {"name": "Golfech-2", "reactor_model": "P'4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 3817, "gross_capacity": 1363, "operational_from": "1993-06-18", "operational_to": None},
        
        # N4 Series (1450 MW)
        {"name": "Chooz-B1", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 4270, "gross_capacity": 1560, "operational_from": "1996-08-30", "operational_to": None},
        {"name": "Chooz-B2", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 4270, "gross_capacity": 1560, "operational_from": "1997-04-10", "operational_to": None},
        {"name": "Civaux-1", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 4270, "gross_capacity": 1561, "operational_from": "1997-12-24", "operational_to": None},
        {"name": "Civaux-2", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "country": "France",
         "thermal_capacity": 4270, "gross_capacity": 1561, "operational_from": "1999-12-24", "operational_to": None},
        
        # EPR (1650 MW)
        {"name": "Flamanville-3", "reactor_model": "EPR", "reactor_type": "PWR", "status": "Under Construction", "country": "France",
         "thermal_capacity": 4590, "gross_capacity": 1650, "operational_from": None, "operational_to": None},
    ]
    
    return pd.DataFrame(reactors)


def generate_maintenance_records(df_reactors: pd.DataFrame, years: int = 10) -> pd.DataFrame:
    """
    Generate realistic maintenance records based on reactor fleet.
    
    Uses equipment MTBF/MTTR to create statistically valid distributions.
    """
    print("🔧 Generating maintenance records...")
    
    np.random.seed(42)
    maintenances = []
    now = datetime.now()
    start_date = now - timedelta(days=365 * years)
    
    operational_reactors = df_reactors[
        df_reactors['status'].isin(['Operational', 'Suspended Operation'])
    ]
    
    for _, reactor in operational_reactors.iterrows():
        # Scale maintenances by reactor capacity
        capacity = reactor.get('gross_capacity', 1000)
        base_maintenances = int(50 + capacity * 0.08 * years)
        
        for _ in range(base_maintenances):
            equipment = np.random.choice(EQUIPMENT_CATALOG)
            
            # Maintenance type distribution varies by equipment criticality
            if equipment['criticality'] == 'high':
                type_probs = [0.70, 0.20, 0.10]  # More preventive
            elif equipment['criticality'] == 'medium':
                type_probs = [0.55, 0.30, 0.15]
            else:
                type_probs = [0.45, 0.35, 0.20]  # More corrective allowed
            
            maintenance_type = np.random.choice(
                ['préventive', 'corrective', 'inspection'],
                p=type_probs
            )
            
            # Duration based on MTTR with variance
            base_duration = equipment['mttr_hours']
            if maintenance_type == 'préventive':
                duration = int(np.random.exponential(base_duration * 0.6))
            elif maintenance_type == 'corrective':
                duration = int(np.random.exponential(base_duration * 1.2))
            else:  # inspection
                duration = int(np.random.exponential(base_duration * 0.3))
            
            duration = max(1, min(duration, 336))  # 1 hour to 2 weeks max
            
            # Random date within range
            days_offset = np.random.randint(0, 365 * years)
            maint_date = start_date + timedelta(days=days_offset)
            
            # Status based on date
            if maint_date > now - timedelta(days=7):
                status = np.random.choice(['pending', 'in_progress', 'completed'], p=[0.4, 0.3, 0.3])
            else:
                status = np.random.choice(['completed', 'cancelled'], p=[0.95, 0.05])
            
            # Cost estimation
            labor_rate = 85  # €/hour
            parts_factor = 1.5 if maintenance_type == 'corrective' else 0.8
            cost = int(duration * labor_rate * parts_factor * np.random.uniform(0.8, 1.3))
            
            maintenances.append({
                'reactor_name': reactor['name'],
                'equipment': equipment['name'],
                'equipment_category': equipment['category'],
                'equipment_criticality': equipment['criticality'],
                'type': maintenance_type,
                'date': maint_date.strftime('%Y-%m-%d'),
                'year': maint_date.year,
                'month': maint_date.month,
                'duration_hours': duration,
                'status': status,
                'cost_euros': cost,
                'technician_count': max(1, int(duration / 8))
            })
    
    df = pd.DataFrame(maintenances)
    print(f"  ✓ Generated {len(df)} maintenance records")
    return df


def generate_incident_records(df_reactors: pd.DataFrame, years: int = 10) -> pd.DataFrame:
    """
    Generate realistic incident records with INES levels and root cause analysis.
    """
    print("⚠️ Generating incident records...")
    
    np.random.seed(42)
    incidents = []
    now = datetime.now()
    start_date = now - timedelta(days=365 * years)
    
    root_causes = [
        "Usure normale des composants",
        "Défaut matériau détecté",
        "Erreur procédurale",
        "Conditions environnementales",
        "Défaillance fournisseur",
        "Interférence électromagnétique",
        "Problème de calibration",
        "Fatigue thermique",
        "Corrosion détectée",
        "En investigation"
    ]
    
    # Reactors that have been operational
    active_reactors = df_reactors[
        df_reactors['status'].isin(['Operational', 'Suspended Operation', 'Shutdown'])
    ]
    
    for _, reactor in active_reactors.iterrows():
        # Fewer incidents than maintenances
        capacity = reactor.get('gross_capacity', 1000)
        n_incidents = int(5 + capacity * 0.015 * years)
        
        for _ in range(n_incidents):
            equipment = np.random.choice(EQUIPMENT_CATALOG)
            
            # Severity based on equipment criticality
            if equipment['criticality'] == 'high':
                severity_probs = [0.60, 0.30, 0.10]
            elif equipment['criticality'] == 'medium':
                severity_probs = [0.70, 0.25, 0.05]
            else:
                severity_probs = [0.80, 0.18, 0.02]
            
            severity = np.random.choice(['low', 'medium', 'high'], p=severity_probs)
            
            # INES level (https://www.iaea.org/topics/emergency-preparedness-and-response-epr/international-nuclear-event-scale)
            if severity == 'low':
                ines_level = 0
            elif severity == 'medium':
                ines_level = np.random.choice([0, 1], p=[0.7, 0.3])
            else:
                ines_level = np.random.choice([1, 2], p=[0.85, 0.15])
            
            # Random date
            days_offset = np.random.randint(0, 365 * years)
            incident_date = start_date + timedelta(days=days_offset)
            
            # Resolution time based on severity
            if severity == 'low':
                resolution_days = max(1, int(np.random.exponential(3)))
            elif severity == 'medium':
                resolution_days = max(3, int(np.random.exponential(14)))
            else:
                resolution_days = max(7, int(np.random.exponential(45)))
            
            resolved = incident_date < now - timedelta(days=resolution_days * 1.5)
            
            # Root cause more likely known if resolved
            if resolved:
                root_cause = np.random.choice(root_causes[:-1])
            else:
                root_cause = np.random.choice(root_causes, p=[0.05]*9 + [0.55])
            
            incidents.append({
                'reactor_name': reactor['name'],
                'equipment': equipment['name'],
                'category': equipment['category'],
                'severity': severity,
                'ines_level': ines_level,
                'date': incident_date.strftime('%Y-%m-%d'),
                'year': incident_date.year,
                'month': incident_date.month,
                'description': f"Incident {severity} sur {equipment['name']} - {equipment['category']}",
                'root_cause': root_cause,
                'resolved': resolved,
                'resolution_days': resolution_days if resolved else None,
                'corrective_actions': np.random.randint(1, 5) if resolved else 0
            })
    
    df = pd.DataFrame(incidents)
    print(f"  ✓ Generated {len(df)} incident records")
    return df


def generate_sensor_timeseries(df_reactors: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """
    Generate realistic sensor time series data for operational reactors.
    """
    print("📊 Generating sensor time series...")
    
    np.random.seed(42)
    sensors = []
    now = datetime.now()
    
    # Sample of operational reactors
    operational = df_reactors[df_reactors['status'] == 'Operational'].head(10)
    
    for _, reactor in operational.iterrows():
        capacity = reactor.get('gross_capacity', 1000)
        
        # Base values with realistic ranges
        base_temp = 290 + np.random.uniform(-5, 5)  # Primary coolant temp
        base_pressure = 155 + np.random.uniform(-2, 2)  # Primary pressure (bar)
        base_power = capacity * 0.95
        
        for hour in range(24 * days):
            timestamp = now - timedelta(hours=24*days - hour)
            
            # Add daily cycle variation
            hour_of_day = hour % 24
            daily_factor = 1 + 0.02 * np.sin(hour_of_day / 24 * 2 * np.pi)
            
            # Add some random walk for realism
            temp_drift = np.random.normal(0, 0.3)
            pressure_drift = np.random.normal(0, 0.1)
            
            # Occasional load following (power variation)
            if np.random.random() < 0.05:
                power_factor = np.random.uniform(0.7, 1.0)
            else:
                power_factor = np.random.uniform(0.92, 1.0)
            
            sensors.append({
                'reactor_name': reactor['name'],
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'date': timestamp.strftime('%Y-%m-%d'),
                'hour': timestamp.hour,
                'primary_temp_celsius': round(base_temp * daily_factor + temp_drift, 2),
                'primary_pressure_bar': round(base_pressure + pressure_drift, 2),
                'power_output_mw': round(base_power * power_factor * daily_factor, 1),
                'coolant_flow_m3h': round(np.random.uniform(18000, 22000), 0),
                'neutron_flux_percent': round(power_factor * 100 + np.random.normal(0, 0.5), 2),
                'containment_pressure_mbar': round(1013 + np.random.normal(0, 2), 1)
            })
    
    df = pd.DataFrame(sensors)
    print(f"  ✓ Generated {len(df)} sensor readings")
    return df


def download_nrc_documents(output_dir: str = "data/docs") -> list:
    """
    Download public NRC inspection reports for RAG corpus.
    """
    print("📄 Downloading NRC public documents...")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    downloaded = []
    
    for doc in NRC_DOCUMENTS:
        try:
            output_path = Path(output_dir) / doc['name']
            
            if output_path.exists():
                print(f"  ℹ {doc['name']} already exists")
                downloaded.append(str(output_path))
                continue
            
            response = requests.get(doc['url'], timeout=60)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ Downloaded {doc['name']}")
                downloaded.append(str(output_path))
            else:
                print(f"  ✗ Failed to download {doc['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error downloading {doc['name']}: {e}")
    
    return downloaded


def build_complete_dataset(
    db_path: str = "data/operational.db",
    years: int = 10,
    download_docs: bool = True
) -> dict:
    """
    Build complete dataset with reactors, maintenances, incidents, and sensors.
    
    Args:
        db_path: Path for SQLite database
        years: Years of historical data to generate
        download_docs: Whether to download NRC documents
        
    Returns:
        Summary dict with counts
    """
    print("\n" + "="*60)
    print("🏭 FRAMATOME AI ASSISTANT - DATA INGESTION PIPELINE")
    print("="*60 + "\n")
    
    # Create data directory
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Get reactor data
    df_reactors = download_geonuclear_data()
    
    # 2. Generate operational data
    df_maintenances = generate_maintenance_records(df_reactors, years)
    df_incidents = generate_incident_records(df_reactors, years)
    df_sensors = generate_sensor_timeseries(df_reactors, days=90)
    
    # 3. Save to SQLite
    print(f"\n💾 Saving to {db_path}...")
    conn = sqlite3.connect(db_path)
    
    df_reactors.to_sql('reactors', conn, if_exists='replace', index=False)
    df_maintenances.to_sql('maintenances', conn, if_exists='replace', index=False)
    df_incidents.to_sql('incidents', conn, if_exists='replace', index=False)
    df_sensors.to_sql('sensor_readings', conn, if_exists='replace', index=False)
    
    # Create equipment catalog table
    df_equipment = pd.DataFrame(EQUIPMENT_CATALOG)
    df_equipment.to_sql('equipment_catalog', conn, if_exists='replace', index=False)
    
    conn.close()
    print("  ✓ Database saved")
    
    # 4. Download documents
    docs_downloaded = []
    if download_docs:
        docs_downloaded = download_nrc_documents()
    
    # Summary
    summary = {
        "reactors": len(df_reactors),
        "maintenances": len(df_maintenances),
        "incidents": len(df_incidents),
        "sensor_readings": len(df_sensors),
        "equipment_types": len(EQUIPMENT_CATALOG),
        "documents_downloaded": len(docs_downloaded),
        "db_path": db_path
    }
    
    print("\n" + "="*60)
    print("✅ DATA INGESTION COMPLETE")
    print("="*60)
    print(f"""
📊 Dataset Summary:
  - Reactors:         {summary['reactors']:,}
  - Maintenances:     {summary['maintenances']:,}
  - Incidents:        {summary['incidents']:,}
  - Sensor readings:  {summary['sensor_readings']:,}
  - Equipment types:  {summary['equipment_types']}
  - Documents:        {summary['documents_downloaded']}
  
💾 Database: {summary['db_path']}
""")
    
    return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build complete operational dataset")
    parser.add_argument("--db-path", default="data/operational.db", help="Database path")
    parser.add_argument("--years", type=int, default=10, help="Years of historical data")
    parser.add_argument("--no-docs", action="store_true", help="Skip document download")
    
    args = parser.parse_args()
    
    build_complete_dataset(
        db_path=args.db_path,
        years=args.years,
        download_docs=not args.no_docs
    )
