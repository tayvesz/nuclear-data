"""
Download Public Documents for RAG Corpus

Downloads public nuclear safety and technical documents from:
- NRC (Nuclear Regulatory Commission)
- IAEA (International Atomic Energy Agency)
- Framatome public documents

These documents form the knowledge base for the DocAgent.
"""

import requests
from pathlib import Path
from typing import List, Dict
import time


# Public documents available for download
PUBLIC_DOCUMENTS = [
    # NRC Inspection Reports
    {
        "url": "https://www.nrc.gov/docs/ML2220/ML22207A388.pdf",
        "name": "NRC_Framatome_Inspection_2022.pdf",
        "doc_type": "inspection",
        "description": "NRC Inspection Report - Framatome Inc. Richland Facility"
    },
    
    # Framatome Public Documents
    {
        "url": "https://www.framatome.com/app/uploads/2022/11/principles-of-conduct-en-2013.pdf",
        "name": "Framatome_Principles_of_Conduct.pdf",
        "doc_type": "policy",
        "description": "Framatome Principles of Conduct"
    },
    
    # IAEA Safety Standards (examples - check actual URLs)
    {
        "url": "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1716web-46541668.pdf",
        "name": "IAEA_Safety_Standards_NS-R-2.pdf",
        "doc_type": "safety",
        "description": "IAEA Safety of Nuclear Power Plants: Design"
    },
]

# Demo technical documents (generated content for testing)
DEMO_DOCUMENTS = [
    {
        "name": "PROC-PUMP-MAINTENANCE-001.txt",
        "doc_type": "procedure",
        "content": """
# PROCÉDURE DE MAINTENANCE DES POMPES PRIMAIRES
## Document: PROC-PUMP-001 Rev.3

### 1. OBJECTIF
Cette procédure définit les étapes de maintenance préventive et corrective 
des pompes du circuit primaire des réacteurs PWR.

### 2. DOMAINE D'APPLICATION
- Pompes primaires principales (RCP)
- Pompes d'injection de sécurité (SI)
- Pompes de refroidissement à l'arrêt (RHR)

### 3. DOCUMENTS DE RÉFÉRENCE
- Spécification technique ST-PUMP-001
- Manuel constructeur Framatome
- Norme RCC-M Section III

### 4. FRÉQUENCE DES INTERVENTIONS

| Type de maintenance | Fréquence | Durée estimée |
|---------------------|-----------|---------------|
| Inspection visuelle | Mensuelle | 2h |
| Contrôle vibratoire | Trimestrielle | 4h |
| Maintenance préventive | Annuelle | 24-48h |
| Révision complète | Tous les 10 ans | 1-2 semaines |

### 5. ÉTAPES DE LA MAINTENANCE PRÉVENTIVE

#### 5.1 Préparation
1. Vérifier l'arrêt de la pompe et la consignation électrique
2. Vidanger le fluide caloporteur
3. Déposer les protections et calorifuges
4. Préparer l'outillage spécifique

#### 5.2 Inspection
5. Contrôle visuel de la volute et du diffuseur
6. Mesure des jeux des paliers (limite: 0.15mm)
7. Contrôle de l'alignement de l'arbre (tolérance: 0.05mm)
8. Inspection des garnitures mécaniques

#### 5.3 Interventions
9. Remplacement des joints toriques
10. Graissage des roulements si applicable
11. Contrôle/remplacement des garnitures
12. Réglage des jeux si nécessaire

#### 5.4 Remontage et tests
13. Remontage dans l'ordre inverse
14. Remplissage et purge du circuit
15. Test de rotation à vide (5 min)
16. Test en charge avec mesure de débit

### 6. CRITÈRES D'ACCEPTATION

| Paramètre | Valeur nominale | Limite |
|-----------|-----------------|--------|
| Vibrations | < 2.5 mm/s | 4.5 mm/s |
| Température paliers | < 70°C | 85°C |
| Débit | ±5% nominal | ±10% |
| Pression différentielle | Selon courbe | ±8% |

### 7. TRAÇABILITÉ
Tous les relevés doivent être consignés dans le registre de maintenance
et le système GMAO (SAP PM).

### 8. SÉCURITÉ
- Port des EPI obligatoire (casque, gants, lunettes)
- Vérification absence de pression résiduelle
- Permis de travail requis pour intervention > 4h
"""
    },
    {
        "name": "SPEC-TEMPERATURE-SENSORS-002.txt",
        "doc_type": "specification",
        "content": """
# SPÉCIFICATION TECHNIQUE DES CAPTEURS DE TEMPÉRATURE
## Document: SPEC-TEMP-002 Rev.5

### 1. OBJET
Spécification des capteurs de température utilisés pour la mesure 
du fluide primaire dans les réacteurs PWR.

### 2. TYPE DE CAPTEURS

#### 2.1 Sondes PT100 Classe A
- Principe: Variation de résistance du platine
- Résistance à 0°C: 100.00 Ω ± 0.06%
- Coefficient: α = 0.00385 Ω/Ω/°C

#### 2.2 Thermocouples Type K
- Principe: Effet Seebeck
- Plage: -200°C à +1250°C
- Précision: ±1.5°C ou ±0.4%

### 3. CARACTÉRISTIQUES TECHNIQUES

| Paramètre | PT100 Classe A | Thermocouple K |
|-----------|----------------|----------------|
| Plage de mesure | -50 à +400°C | -40 à +600°C |
| Précision | ±(0.15 + 0.002×T)°C | ±1.5°C |
| Temps de réponse | < 5s (τ63%) | < 3s |
| Pression max | 160 bar | 200 bar |
| Durée de vie | 10 ans | 5 ans |

### 4. CONDITIONS D'INSTALLATION

#### 4.1 Environnement
- Température ambiante: -10°C à +50°C
- Humidité relative: < 95% sans condensation
- Vibrations: < 10 m/s² (10-500 Hz)

#### 4.2 Montage
- Doigt de gant en Inconel 690
- Immersion minimum: 100mm
- Orientation: ±30° de la verticale

### 5. ÉTALONNAGE

#### 5.1 Fréquence
- Étalonnage initial: avant mise en service
- Étalonnage périodique: annuel
- Étalonnage après incident

#### 5.2 Points de calibration
| Point | Température | Tolérance |
|-------|-------------|-----------|
| Glace fondante | 0.00°C | ±0.02°C |
| Eau bouillante | 100.00°C | ±0.05°C |
| Référence 200°C | 200.00°C | ±0.10°C |
| Référence 300°C | 300.00°C | ±0.15°C |

### 6. CRITÈRES DE REMPLACEMENT
- Dérive > 0.5°C confirmée
- Temps de réponse > 10s
- Isolation électrique < 100 MΩ
- Dommage mécanique visible
- Fin de durée de vie qualifiée

### 7. RÉFÉRENCES
- IEC 60751 - Thermomètres à résistance de platine
- IEC 60584 - Thermocouples
- RCC-E - Règles de conception électrique
"""
    },
    {
        "name": "RAPPORT-INSPECTION-SEMESTRIELLE-2024.txt",
        "doc_type": "rapport",
        "content": """
# RAPPORT D'INSPECTION SEMESTRIELLE
## Centrale: Civaux - Tranche 1
## Période: Janvier - Juin 2024
## Document: RAP-INSP-2024-S1-CIV1

### RÉSUMÉ EXÉCUTIF

L'inspection semestrielle de la tranche 1 de Civaux confirme le bon état 
général des équipements. Le taux de disponibilité de 96.8% est conforme 
aux objectifs. Trois écarts mineurs ont été identifiés et traités.

---

### 1. INDICATEURS CLÉS DE PERFORMANCE

| Indicateur | Objectif | Réalisé | Statut |
|------------|----------|---------|--------|
| Disponibilité | > 95% | 96.8% | ✅ |
| MTBF moyen | > 2000h | 2340h | ✅ |
| Incidents INES 0 | < 5 | 3 | ✅ |
| Incidents INES 1+ | 0 | 0 | ✅ |
| Maintenances préventives | 100% | 98% | ⚠️ |

---

### 2. ÉVÉNEMENTS SIGNIFICATIFS

#### 2.1 Incident du 15 février 2024
- **Description**: Arrêt automatique réacteur sur signal bas niveau GV
- **Cause racine**: Dérive capteur niveau P-125
- **Sévérité**: INES 0 (écart sans impact sûreté)
- **Actions correctives**: 
  - Recalibration capteur effectuée
  - Renforcement surveillance mensuelle
  
#### 2.2 Anomalie du 8 avril 2024
- **Description**: Fuite mineure sur joint de vanne 1VP-023
- **Débit fuite**: 0.5 L/h (limite: 5 L/h)
- **Actions**: Resserrage en service, remplacement programmé

---

### 3. BILAN DES MAINTENANCES

#### 3.1 Maintenances préventives réalisées
| Équipement | Nombre | Conformité |
|------------|--------|------------|
| Pompes | 24 | 100% |
| Vannes | 156 | 97% |
| Capteurs | 89 | 100% |
| Systèmes élec. | 45 | 96% |

#### 3.2 Maintenances correctives
- Total: 18 interventions
- Durée moyenne: 4.2 heures
- Délai moyen d'intervention: 1.8 heures

---

### 4. CONTRÔLES NON DESTRUCTIFS

| Type de contrôle | Nombre | Indications | Acceptables |
|------------------|--------|-------------|-------------|
| Ultrasons | 34 | 2 | 2 |
| Radiographie | 12 | 0 | - |
| Ressuage | 28 | 1 | 1 |
| Magnétoscopie | 15 | 0 | - |

---

### 5. RECOMMANDATIONS

1. **Priorité haute**: Planifier remplacement capteur P-125 lors 
   du prochain arrêt programmé (ASR 2024)

2. **Priorité moyenne**: Renforcer le programme de contrôle des 
   vannes de la boucle 2 (3 écarts identifiés)

3. **Information**: Mettre à jour la procédure PROC-CAL-001 suite 
   aux retours d'expérience du semestre

---

### 6. CONCLUSION

La tranche 1 de Civaux a maintenu un niveau de performance satisfaisant 
durant le premier semestre 2024. Les écarts identifiés sont de niveau 
mineur et font l'objet d'un suivi approprié.

**Prochaine inspection**: Juillet 2024

---
Approuvé par: Chef d'Exploitation - Civaux
Date: 2024-07-01
"""
    },
    {
        "name": "GUIDE-SURETE-DEFENSE-PROFONDEUR.txt",
        "doc_type": "safety",
        "content": """
# GUIDE DE SÛRETÉ NUCLÉAIRE
## Concept de Défense en Profondeur
## Document: GUIDE-SUR-001 Rev.2

### 1. PRINCIPE FONDAMENTAL

La défense en profondeur est le concept de sûreté central des installations 
nucléaires. Elle repose sur plusieurs niveaux successifs de protection 
et barrières pour prévenir les accidents et en limiter les conséquences.

---

### 2. LES CINQ NIVEAUX DE DÉFENSE

#### Niveau 1: Prévention des anomalies
- Conception robuste et marges de sûreté
- Qualité de construction (RCC-M, RCC-E)
- Qualification des équipements
- Formation et compétence du personnel

#### Niveau 2: Surveillance et protection
- Systèmes de régulation automatique
- Systèmes de limitation
- Alarmes et signalisations
- Procédures d'exploitation normale

#### Niveau 3: Gestion des accidents de référence
- Systèmes de sauvegarde (injection de sécurité)
- Systèmes de refroidissement de secours
- Enceinte de confinement
- Procédures incidentelles/accidentelles

#### Niveau 4: Gestion des accidents graves
- Prévention de la fusion du cœur
- Récupérateur de corium (EPR)
- Filtration des rejets
- Plan d'urgence interne (PUI)

#### Niveau 5: Atténuation des conséquences
- Plan particulier d'intervention (PPI)
- Évacuation et mise à l'abri
- Distribution d'iode
- Gestion post-accidentelle

---

### 3. LES TROIS BARRIÈRES DE CONFINEMENT

```
┌─────────────────────────────────────────┐
│        Enceinte de confinement          │  ← 3ème barrière
│  ┌─────────────────────────────────┐    │
│  │    Circuit primaire             │    │  ← 2ème barrière
│  │  ┌─────────────────────────┐    │    │
│  │  │   Gaine combustible     │    │    │  ← 1ère barrière
│  │  │  ┌─────────────────┐    │    │    │
│  │  │  │  Pastilles UO2  │    │    │    │
│  │  │  └─────────────────┘    │    │    │
│  │  └─────────────────────────┘    │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

#### 3.1 Première barrière: Gaine du combustible
- Matériau: Alliage de zirconium (Zircaloy-4, M5)
- Épaisseur: 0.57 mm
- Fonction: Retient les produits de fission gazeux

#### 3.2 Deuxième barrière: Enveloppe du circuit primaire
- Matériau: Acier inoxydable austénitique
- Pression de service: 155 bar
- Fonction: Confine le fluide caloporteur

#### 3.3 Troisième barrière: Enceinte de confinement
- Type: Béton précontraint + peau métallique
- Pression de dimensionnement: 5.2 bar abs
- Fonction: Dernière barrière avant environnement

---

### 4. FONCTIONS DE SÛRETÉ

#### 4.1 Contrôle de la réactivité
- Grappes de commande (absorbants)
- Bore soluble
- Arrêt automatique réacteur (AAR)

#### 4.2 Évacuation de la puissance résiduelle
- Générateurs de vapeur
- Circuit de refroidissement (RRA/RRI)
- Aspersion de secours (EAS)

#### 4.3 Confinement des matières radioactives
- Intégrité des trois barrières
- Ventilation filtrée
- Contrôle de la pression enceinte

---

### 5. ÉCHELLE INES

| Niveau | Dénomination | Exemple |
|--------|--------------|---------|
| 0 | Écart | Défaut mineur sans impact |
| 1 | Anomalie | Écart aux spécifications |
| 2 | Incident | Défaillance importante |
| 3 | Incident grave | Contamination localisée |
| 4 | Accident sans risque ext. | TMI (1979) |
| 5 | Accident avec risque ext. | Windscale (1957) |
| 6 | Accident grave | Kychtym (1957) |
| 7 | Accident majeur | Tchernobyl, Fukushima |

---

### 6. RÉFÉRENCES RÉGLEMENTAIRES

- Arrêté INB du 7 février 2012
- Décision ASN 2014-DC-0444 (ESS)
- Guide ASN n°22 (Conception)
- Règles fondamentales de sûreté (RFS)
"""
    },
]


def download_public_documents(output_dir: str = "data/docs") -> List[str]:
    """
    Download public documents from NRC, IAEA, Framatome.
    
    Args:
        output_dir: Directory to save documents
        
    Returns:
        List of downloaded file paths
    """
    print("📥 Downloading public documents for RAG...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    
    for doc in PUBLIC_DOCUMENTS:
        try:
            file_path = output_path / doc['name']
            
            if file_path.exists():
                print(f"  ℹ {doc['name']} already exists, skipping")
                downloaded.append(str(file_path))
                continue
            
            print(f"  📄 Downloading {doc['name']}...")
            response = requests.get(doc['url'], timeout=60, allow_redirects=True)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"     ✓ Downloaded ({len(response.content) / 1024:.1f} KB)")
                downloaded.append(str(file_path))
            else:
                print(f"     ✗ Failed: HTTP {response.status_code}")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    return downloaded


def create_demo_documents(output_dir: str = "data/docs") -> List[str]:
    """
    Create demo technical documents for testing without external downloads.
    
    Args:
        output_dir: Directory to save documents
        
    Returns:
        List of created file paths
    """
    print("📝 Creating demo technical documents...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    created = []
    
    for doc in DEMO_DOCUMENTS:
        try:
            file_path = output_path / doc['name']
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
            
            print(f"  ✓ Created {doc['name']} ({doc['doc_type']})")
            created.append(str(file_path))
            
        except Exception as e:
            print(f"  ✗ Error creating {doc['name']}: {e}")
    
    return created


def setup_document_corpus(output_dir: str = "data/docs", include_downloads: bool = True) -> dict:
    """
    Set up complete document corpus for RAG.
    
    Args:
        output_dir: Directory for documents
        include_downloads: Whether to attempt downloading public docs
        
    Returns:
        Summary dict
    """
    print("\n" + "="*50)
    print("📚 DOCUMENT CORPUS SETUP")
    print("="*50 + "\n")
    
    # Create demo documents (always)
    demo_docs = create_demo_documents(output_dir)
    
    # Download public documents (optional)
    downloaded_docs = []
    if include_downloads:
        downloaded_docs = download_public_documents(output_dir)
    
    # Summary
    all_docs = demo_docs + downloaded_docs
    
    summary = {
        "total_documents": len(all_docs),
        "demo_documents": len(demo_docs),
        "downloaded_documents": len(downloaded_docs),
        "output_directory": output_dir,
        "files": all_docs
    }
    
    print(f"\n✅ Document corpus ready:")
    print(f"   - Demo documents: {len(demo_docs)}")
    print(f"   - Downloaded: {len(downloaded_docs)}")
    print(f"   - Total: {len(all_docs)}")
    print(f"   - Location: {output_dir}")
    
    return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download documents for RAG")
    parser.add_argument("--output-dir", default="data/docs", help="Output directory")
    parser.add_argument("--no-download", action="store_true", help="Skip external downloads")
    
    args = parser.parse_args()
    
    setup_document_corpus(
        output_dir=args.output_dir,
        include_downloads=not args.no_download
    )
