import random
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta

fake = Faker("fr_FR")
random.seed(42)
np.random.seed(42)

produits = [
    ("Laptop Pro 15","Informatique","Ordinateurs",899.99,"TechCorp"),
    ("Smartphone X12","Informatique","Telephones",549.00,"PhoneWorld"),
    ("Ecran 4K","Informatique","Ecrans",349.99,"ViewTech"),
    ("Imprimante Laser","Informatique","Peripheriques",199.00,"PrintPro"),
    ("Clavier Meca","Informatique","Peripheriques",89.99,"KeyMaster"),
    ("Canape 3 places","Mobilier","Salon",599.00,"FurniHome"),
    ("Table manger","Mobilier","Salle manger",349.00,"WoodStyle"),
    ("Chaise bureau","Mobilier","Bureau",149.99,"ErgoSeat"),
    ("Lampe LED","Maison","Eclairage",49.99,"LightUp"),
    ("Robot cuiseur","Electromenager","Cuisine",349.00,"CookBot"),
    ("Aspirateur robot","Electromenager","Nettoyage",299.99,"CleanBot"),
    ("Machine cafe","Electromenager","Cuisine",199.00,"BrewMaster"),
]
magasins = [
    ("Hypermarche Lyon","Lyon","Auvergne-Rhone",8000,"Hypermarche"),
    ("Super Bordeaux","Bordeaux","Nouvelle-Aquitaine",3500,"Supermarche"),
    ("Drive Paris","Paris","Ile-de-France",500,"Drive"),
    ("Mega Marseille","Marseille","Provence-PACA",6000,"Hypermarche"),
    ("Super Toulouse","Toulouse","Occitanie",4000,"Supermarche"),
    ("Drive Nantes","Nantes","Pays de la Loire",600,"Drive"),
]

DATE_DEBUT = date(2022, 1, 1)
DATE_FIN   = date(2024, 12, 31)
delta = (DATE_FIN - DATE_DEBUT).days

lignes = []
for _ in range(5000):
    p = random.choice(produits)
    m = random.choice(magasins)
    q = random.choices([1,2,3,5], weights=[60,25,10,5])[0]
    r = round(random.choices([0,5,10,15,20], weights=[40,25,20,10,5])[0], 2)
    ht  = round(q * p[3] * (1 - r/100), 2)
    ttc = round(ht * 1.2, 2)
    d   = DATE_DEBUT + timedelta(days=random.randint(0, delta))
    lignes.append({
        "date": d, "nom_produit": p[0], "categorie": p[1],
        "sous_categorie": p[2], "prix_unitaire": p[3], "fournisseur": p[4],
        "nom_client": fake.last_name(), "prenom_client": fake.first_name(),
        "ville_client": fake.city(),
        "nom_magasin": m[0], "ville_magasin": m[1], "region_magasin": m[2],
        "surface_m2": m[3], "type_magasin": m[4],
        "quantite": q, "remise_pct": r, "montant_ht": ht, "montant_ttc": ttc,
        "marge": round(ht * random.uniform(0.15, 0.40), 2),
    })

df = pd.DataFrame(lignes)

def esc(s):
    return str(s).replace("'", "''")

lines = ["TRUNCATE fait_ventes,dim_client,dim_temps,dim_produit,dim_magasin RESTART IDENTITY CASCADE;"]

# dim_temps
for d in df["date"].drop_duplicates():
    j=d.day; mo=d.month; t=(mo-1)//3+1; a=d.year
    ew = 1 if d.weekday() >= 5 else 0
    nm = d.strftime("%B"); js = d.strftime("%A")
    lines.append(
        "INSERT INTO dim_temps (date_complete,jour,mois,trimestre,annee,nom_mois,jour_semaine,est_weekend) "
        "VALUES ('" + str(d) + "'," + str(j) + "," + str(mo) + "," + str(t) + "," + str(a) +
        ",'" + nm + "','" + js + "'," + str(ew) + ") ON CONFLICT DO NOTHING;"
    )

# dim_produit
for _, row in df[["nom_produit","categorie","sous_categorie","prix_unitaire","fournisseur"]].drop_duplicates("nom_produit").iterrows():
    lines.append(
        "INSERT INTO dim_produit (nom_produit,categorie,sous_categorie,prix_unitaire,fournisseur) VALUES ('"
        + esc(row.nom_produit) + "','" + esc(row.categorie) + "','" + esc(row.sous_categorie) + "',"
        + str(row.prix_unitaire) + ",'" + esc(row.fournisseur) + "') ON CONFLICT DO NOTHING;"
    )

# dim_magasin
for _, row in df[["nom_magasin","ville_magasin","region_magasin","surface_m2","type_magasin"]].drop_duplicates("nom_magasin").iterrows():
    lines.append(
        "INSERT INTO dim_magasin (nom_magasin,ville,region,surface_m2,type_magasin) VALUES ('"
        + esc(row.nom_magasin) + "','" + esc(row.ville_magasin) + "','" + esc(row.region_magasin) + "',"
        + str(int(row.surface_m2)) + ",'" + esc(row.type_magasin) + "') ON CONFLICT DO NOTHING;"
    )

# dim_client
for _, row in df.iterrows():
    lines.append(
        "INSERT INTO dim_client (nom,prenom,age,genre,segment,ville,region) VALUES ('"
        + esc(row.nom_client) + "','" + esc(row.prenom_client) + "',30,'M','Standard','"
        + esc(row.ville_client) + "','France');"
    )

# fait_ventes (on insere apres avoir les IDs via SELECT)
lines.append("""
DO $$
DECLARE
  v_it INTEGER; v_ip INTEGER; v_ic INTEGER; v_im INTEGER;
BEGIN
""")

for _, row in df.iterrows():
    lines.append(
        "  SELECT id_temps INTO v_it FROM dim_temps WHERE date_complete='" + str(row["date"]) + "';"
        + " SELECT id_produit INTO v_ip FROM dim_produit WHERE nom_produit='" + esc(row.nom_produit) + "';"
        + " SELECT id_magasin INTO v_im FROM dim_magasin WHERE nom_magasin='" + esc(row.nom_magasin) + "';"
        + " SELECT id_client INTO v_ic FROM dim_client WHERE nom='" + esc(row.nom_client) + "' AND prenom='" + esc(row.prenom_client) + "' LIMIT 1;"
        + " INSERT INTO fait_ventes (id_temps,id_produit,id_client,id_magasin,quantite,prix_unitaire,remise_pct,montant_ht,montant_ttc,marge)"
        + " VALUES (v_it,v_ip,v_ic,v_im," + str(int(row.quantite)) + "," + str(float(row.prix_unitaire)) + ","
        + str(float(row.remise_pct)) + "," + str(float(row.montant_ht)) + "," + str(float(row.montant_ttc)) + "," + str(float(row.marge)) + ");"
    )

lines.append("END $$;")

with open("data/load.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("OK : data/load.sql genere - " + str(len(lines)) + " lignes")
