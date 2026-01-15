"""
Seed Operational Database - Generate Realistic Nuclear Plant Data

Creates SQLite database with simulated operational data including:
- Reactors (from GeoNuclearData or simulated)
- Maintenance records
- Incident reports
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import numpy as np
import requests
import os


# Reactor data - simulated based on real French nuclear fleet
FRENCH_REACTORS = [
    {"name": "Belleville-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Belleville-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Blayais-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 951},
    {"name": "Blayais-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 951},
    {"name": "Bugey-2", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 945},
    {"name": "Bugey-3", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 945},
    {"name": "Cattenom-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1362},
    {"name": "Cattenom-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1362},
    {"name": "Chinon-B1", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 954},
    {"name": "Chinon-B2", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 954},
    {"name": "Civaux-1", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 4270, "gross_capacity": 1561},
    {"name": "Civaux-2", "reactor_model": "N4", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 4270, "gross_capacity": 1561},
    {"name": "Cruas-1", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 956},
    {"name": "Cruas-2", "reactor_model": "CP2", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 956},
    {"name": "Dampierre-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 937},
    {"name": "Dampierre-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 937},
    {"name": "Fessenheim-1", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Shutdown", "thermal_capacity": 2660, "gross_capacity": 920},
    {"name": "Fessenheim-2", "reactor_model": "CP0", "reactor_type": "PWR", "status": "Shutdown", "thermal_capacity": 2660, "gross_capacity": 920},
    {"name": "Flamanville-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
    {"name": "Flamanville-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
    {"name": "Flamanville-3", "reactor_model": "EPR", "reactor_type": "PWR", "status": "Under Construction", "thermal_capacity": 4590, "gross_capacity": 1650},
    {"name": "Golfech-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Golfech-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Gravelines-1", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 951},
    {"name": "Gravelines-2", "reactor_model": "CP1", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 2785, "gross_capacity": 951},
    {"name": "Nogent-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Nogent-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1363},
    {"name": "Paluel-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
    {"name": "Paluel-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
    {"name": "Penly-1", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
    {"name": "Penly-2", "reactor_model": "P4 REP 1300", "reactor_type": "PWR", "status": "Operational", "thermal_capacity": 3817, "gross_capacity": 1382},
]

# Equipment types with failure probabilities
EQUIPMENT_TYPES = [
    {"name": "Pompe primaire", "category": "mécanique", "mtbf_hours": 8760, "mttr_hours": 24},
    {"name": "Vanne de régulation", "category": "mécanique", "mtbf_hours": 4380, "mttr_hours": 8},
    {"name": "Capteur température", "category": "instrumentation", "mtbf_hours": 17520, "mttr_hours": 4},
    {"name": "Capteur pression", "category": "instrumentation", "mtbf_hours": 17520, "mttr_hours": 4},
    {"name": "Générateur diesel", "category": "électrique", "mtbf_hours": 2190, "mttr_hours": 48},
    {"name": "Transformateur", "category": "électrique", "mtbf_hours": 43800, "mttr_hours": 72},
    {"name": "Échangeur thermique", "category": "thermique", "mtbf_hours": 26280, "mttr_hours": 36},
    {"name": "Turbine", "category": "mécanique", "mtbf_hours": 8760, "mttr_hours": 120},
    {"name": "Moteur électrique", "category": "électrique", "mtbf_hours": 13140, "mttr_hours": 16},
    {"name": "Système contrôle-commande", "category": "instrumentation", "mtbf_hours": 8760, "mttr_hours": 12},
]


def seed_database(db_path: str = "data/operational.db", years_of_data: int = 5) -> None:
    """
    Seed the operational database with realistic simulated data.
    
    Args:
        db_path: Path to SQLite database
        years_of_data: Number of years of historical data to generate
    """
    np.random.seed(42)  # Reproducibility
    
    # Create data directory
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    print("🔧 Generating operational database...")
    
    conn = sqlite3.connect(db_path)
    
    # 1. Create reactors table
    print("  📍 Creating reactors table...")
    df_reactors = pd.DataFrame(FRENCH_REACTORS)
    
    # Add operational dates
    df_reactors["country"] = "France"
    df_reactors["operational_from"] = [
        f"{np.random.randint(1977, 2015)}-01-01" 
        for _ in range(len(df_reactors))
    ]
    df_reactors.loc[df_reactors["status"] == "Under Construction", "operational_from"] = None
    
    df_reactors.to_sql("reactors", conn, if_exists="replace", index=False)
    print(f"     ✓ {len(df_reactors)} reactors")
    
    # 2. Generate maintenance records
    print("  🔧 Generating maintenance records...")
    maintenances = []
    
    now = datetime.now()
    start_date = now - timedelta(days=365 * years_of_data)
    
    for reactor in FRENCH_REACTORS:
        if reactor["status"] not in ["Operational", "Shutdown"]:
            continue
        
        # Number of maintenances based on capacity
        n_maintenances = int(100 + reactor["gross_capacity"] * 0.05 * years_of_data)
        
        for _ in range(n_maintenances):
            equipment = np.random.choice(EQUIPMENT_TYPES)
            maintenance_type = np.random.choice(
                ["préventive", "corrective", "inspection"],
                p=[0.55, 0.30, 0.15]
            )
            
            # Duration based on equipment MTTR
            base_duration = equipment["mttr_hours"]
            duration = max(1, int(np.random.exponential(base_duration * 0.5)))
            
            date = start_date + timedelta(
                days=np.random.randint(0, 365 * years_of_data)
            )
            
            maintenances.append({
                "reactor_name": reactor["name"],
                "equipment": equipment["name"],
                "equipment_category": equipment["category"],
                "type": maintenance_type,
                "date": date.strftime("%Y-%m-%d"),
                "duration_hours": min(duration, 168),  # Cap at 1 week
                "status": np.random.choice(
                    ["completed", "pending", "in_progress"],
                    p=[0.85, 0.10, 0.05]
                ),
                "cost_euros": int(duration * np.random.uniform(500, 2000))
            })
    
    df_maintenances = pd.DataFrame(maintenances)
    df_maintenances.to_sql("maintenances", conn, if_exists="replace", index=False)
    print(f"     ✓ {len(df_maintenances)} maintenance records")
    
    # 3. Generate incidents
    print("  ⚠️ Generating incident records...")
    incidents = []
    
    for reactor in FRENCH_REACTORS:
        if reactor["status"] not in ["Operational", "Shutdown"]:
            continue
        
        # Fewer incidents than maintenances
        n_incidents = int(10 + reactor["gross_capacity"] * 0.01 * years_of_data)
        
        for _ in range(n_incidents):
            equipment = np.random.choice(EQUIPMENT_TYPES)
            
            # Severity based on equipment criticality
            if equipment["category"] == "instrumentation":
                severity_probs = [0.70, 0.25, 0.05]
            elif equipment["category"] == "électrique":
                severity_probs = [0.60, 0.30, 0.10]
            else:
                severity_probs = [0.65, 0.28, 0.07]
            
            severity = np.random.choice(["low", "medium", "high"], p=severity_probs)
            
            date = start_date + timedelta(
                days=np.random.randint(0, 365 * years_of_data)
            )
            
            # Resolution time based on severity
            resolution_days = {
                "low": np.random.randint(1, 7),
                "medium": np.random.randint(3, 30),
                "high": np.random.randint(7, 90)
            }
            
            resolved = np.random.choice([True, False], p=[0.90, 0.10])
            
            incidents.append({
                "reactor_name": reactor["name"],
                "equipment": equipment["name"],
                "category": equipment["category"],
                "severity": severity,
                "ines_level": 0 if severity == "low" else (1 if severity == "medium" else np.random.choice([1, 2], p=[0.8, 0.2])),
                "date": date.strftime("%Y-%m-%d"),
                "description": f"Incident sur {equipment['name']} - {severity}",
                "resolved": resolved,
                "resolution_days": resolution_days[severity] if resolved else None,
                "root_cause": np.random.choice([
                    "Usure normale",
                    "Défaut matériau",
                    "Erreur humaine",
                    "Conditions environnementales",
                    "Défaillance fournisseur",
                    "En investigation"
                ], p=[0.30, 0.15, 0.10, 0.15, 0.10, 0.20])
            })
    
    df_incidents = pd.DataFrame(incidents)
    df_incidents.to_sql("incidents", conn, if_exists="replace", index=False)
    print(f"     ✓ {len(df_incidents)} incident records")
    
    # 4. Generate sensor readings (sample time series)
    print("  📊 Generating sensor readings...")
    sensors = []
    
    # Generate 30 days of hourly readings for a few reactors
    sample_reactors = FRENCH_REACTORS[:5]
    for reactor in sample_reactors:
        if reactor["status"] != "Operational":
            continue
        
        base_temp = 290 + np.random.uniform(-5, 5)  # Base primary temperature
        base_pressure = 155 + np.random.uniform(-2, 2)  # Base pressure in bar
        
        for hour in range(24 * 30):  # 30 days
            timestamp = now - timedelta(hours=24*30 - hour)
            
            # Add realistic variations
            temp_variation = np.sin(hour / 24 * 2 * np.pi) * 2 + np.random.normal(0, 0.5)
            pressure_variation = np.random.normal(0, 0.3)
            
            sensors.append({
                "reactor_name": reactor["name"],
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "primary_temp_celsius": round(base_temp + temp_variation, 2),
                "primary_pressure_bar": round(base_pressure + pressure_variation, 2),
                "power_output_mw": round(reactor["gross_capacity"] * np.random.uniform(0.85, 1.0), 1),
                "coolant_flow_m3h": round(np.random.uniform(18000, 22000), 0)
            })
    
    df_sensors = pd.DataFrame(sensors)
    df_sensors.to_sql("sensor_readings", conn, if_exists="replace", index=False)
    print(f"     ✓ {len(df_sensors)} sensor readings")
    
    conn.close()
    
    print(f"\n✅ Database created at {db_path}")
    print(f"   Tables: reactors, maintenances, incidents, sensor_readings")


def load_operational_data(db_path: str = "data/operational.db") -> dict:
    """
    Load operational data from database into DataFrames.
    
    Returns:
        Dict with table names as keys and DataFrames as values
    """
    if not Path(db_path).exists():
        print(f"⚠️ Database not found at {db_path}, creating...")
        seed_database(db_path)
    
    conn = sqlite3.connect(db_path)
    
    data = {}
    
    # Load all tables
    tables = ["reactors", "maintenances", "incidents", "sensor_readings"]
    for table in tables:
        try:
            data[table] = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        except Exception as e:
            print(f"⚠️ Could not load {table}: {e}")
            data[table] = pd.DataFrame()
    
    conn.close()
    
    return data


def get_db_summary(db_path: str = "data/operational.db") -> str:
    """Get a summary of the database contents."""
    if not Path(db_path).exists():
        return "Database not found"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    summary = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        summary.append(f"- {table_name}: {count:,} rows")
    
    conn.close()
    
    return "\n".join(summary)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed operational database")
    parser.add_argument("--db-path", default="data/operational.db", help="Database path")
    parser.add_argument("--years", type=int, default=5, help="Years of historical data")
    
    args = parser.parse_args()
    
    seed_database(db_path=args.db_path, years_of_data=args.years)
    
    print("\n" + "="*50)
    print("Database Summary:")
    print(get_db_summary(args.db_path))
