import os, random, sqlite3
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta
import pg8000.native

os.environ["PGSERVICEFILE"] = ""
os.environ["PGSYSCONFDIR"]  = ""

DB_SQLITE = "data/datawarehouse.db"
DB_PG = dict(host="localhost", port=5432, database="datawarehouse", user="dw_user", password="dw_pass123")

NB_LIGNES = 5000
DATE_DEBUT = date(2022, 1, 1)
DATE_FIN   = date(2024, 12, 31)
fake = Faker("fr_FR")
random.seed(42); np.random.seed(42)

def generer_csv(chemin="data/ventes_raw.csv"):
    produits=[("Laptop Pro 15","Informatique","Ordinateurs",899.99,"TechCorp"),("Smartphone X12","Informatique","Telephones",549.00,"PhoneWorld"),("Ecran 4K","Informatique","Ecrans",349.99,"ViewTech"),("Imprimante Laser","Informatique","Peripheriques",199.00,"PrintPro"),("Clavier Meca","Informatique","Peripheriques",89.99,"KeyMaster"),("Canape 3 places","Mobilier","Salon",599.00,"FurniHome"),("Table manger","Mobilier","Salle manger",349.00,"WoodStyle"),("Chaise bureau","Mobilier","Bureau",149.99,"ErgoSeat"),("Lampe LED","Maison","Eclairage",49.99,"LightUp"),("Robot cuiseur","Electromenager","Cuisine",349.00,"CookBot"),("Aspirateur robot","Electromenager","Nettoyage",299.99,"CleanBot"),("Machine cafe","Electromenager","Cuisine",199.00,"BrewMaster")]
    magasins=[("Hypermarche Lyon","Lyon","Auvergne-Rhone",8000,"Hypermarche"),("Super Bordeaux","Bordeaux","Nouvelle-Aquitaine",3500,"Supermarche"),("Drive Paris","Paris","Ile-de-France",500,"Drive"),("Mega Marseille","Marseille","Provence-PACA",6000,"Hypermarche"),("Super Toulouse","Toulouse","Occitanie",4000,"Supermarche"),("Drive Nantes","Nantes","Pays de la Loire",600,"Drive")]
    lignes=[]; delta=(DATE_FIN-DATE_DEBUT).days
    for _ in range(NB_LIGNES):
        p=random.choice(produits); m=random.choice(magasins)
        q=random.choices([1,2,3,5],weights=[60,25,10,5])[0]
        r=round(random.choices([0,5,10,15,20],weights=[40,25,20,10,5])[0],2)
        ht=round(q*p[3]*(1-r/100),2); ttc=round(ht*1.2,2)
        lignes.append({"date":DATE_DEBUT+timedelta(days=random.randint(0,delta)),"nom_produit":p[0],"categorie":p[1],"sous_categorie":p[2],"prix_unitaire":p[3],"fournisseur":p[4],"nom_client":fake.last_name(),"prenom_client":fake.first_name(),"age_client":random.randint(18,75),"genre_client":random.choice(["M","F"]),"ville_client":fake.city(),"region_client":"France","nom_magasin":m[0],"ville_magasin":m[1],"region_magasin":m[2],"surface_m2":m[3],"type_magasin":m[4],"quantite":q,"remise_pct":r,"montant_ht":ht,"montant_ttc":ttc,"marge":round(ht*random.uniform(0.15,0.40),2)})
    df=pd.DataFrame(lignes); df.to_csv(chemin,index=False,encoding="utf-8")
    print(f"   OK : {len(df)} lignes"); return df

def transformer(df):
    avant=len(df)
    df=df.dropna(subset=["date","nom_produit","quantite"]).drop_duplicates(subset=["date","nom_produit","nom_client","quantite"])
    df["nom_client"]=df["nom_client"].str.strip().str.title(); df["prenom_client"]=df["prenom_client"].str.strip().str.title()
    df["date"]=pd.to_datetime(df["date"]); df["jour"]=df["date"].dt.day; df["mois"]=df["date"].dt.month
    df["trimestre"]=df["date"].dt.quarter; df["annee"]=df["date"].dt.year
    df["nom_mois"]=df["date"].dt.strftime("%B"); df["jour_semaine"]=df["date"].dt.strftime("%A")
    df["est_weekend"]=(df["date"].dt.dayofweek>=5).astype(int)
    df["segment_client"]=pd.cut(df["montant_ttc"],bins=[0,100,500,9999],labels=["Occasionnel","Standard","Premium"]).astype(str)
    print(f"   OK : {avant} -> {len(df)} lignes"); return df

def charger_pg(df):
    print("\nChargement PostgreSQL...")
    conn=pg8000.native.Connection(**DB_PG)
    dates=df[["date","jour","mois","trimestre","annee","nom_mois","jour_semaine","est_weekend"]].drop_duplicates("date")
    for r in dates.itertuples():
        conn.run("INSERT INTO dim_temps (date_complete,jour,mois,trimestre,annee,nom_mois,jour_semaine,est_weekend) VALUES (:a,:b,:c,:d,:e,:f,:g,:h) ON CONFLICT (date_complete) DO NOTHING",a=str(r.date.date()),b=int(r.jour),c=int(r.mois),d=int(r.trimestre),e=int(r.annee),f=r.nom_mois,g=r.jour_semaine,h=int(r.est_weekend))
    print(f"   OK dim_temps : {len(dates)}")
    prods=df[["nom_produit","categorie","sous_categorie","prix_unitaire","fournisseur"]].drop_duplicates("nom_produit")
    for r in prods.itertuples():
        conn.run("INSERT INTO dim_produit (nom_produit,categorie,sous_categorie,prix_unitaire,fournisseur) VALUES (:a,:b,:c,:d,:e) ON CONFLICT DO NOTHING",a=r.nom_produit,b=r.categorie,c=r.sous_categorie,d=float(r.prix_unitaire),e=r.fournisseur)
    print(f"   OK dim_produit : {len(prods)}")
    clients=df[["nom_client","prenom_client","age_client","genre_client","segment_client","ville_client","region_client"]].drop_duplicates()
    for r in clients.itertuples():
        conn.run("INSERT INTO dim_client (nom,prenom,age,genre,segment,ville,region) VALUES (:a,:b,:c,:d,:e,:f,:g)",a=r.nom_client,b=r.prenom_client,c=int(r.age_client),d=r.genre_client,e=r.segment_client,f=r.ville_client,g=r.region_client)
    print(f"   OK dim_client : {len(clients)}")
    mags=df[["nom_magasin","ville_magasin","region_magasin","surface_m2","type_magasin"]].drop_duplicates("nom_magasin")
    for r in mags.itertuples():
        conn.run("INSERT INTO dim_magasin (nom_magasin,ville,region,surface_m2,type_magasin) VALUES (:a,:b,:c,:d,:e) ON CONFLICT DO NOTHING",a=r.nom_magasin,b=r.ville_magasin,c=r.region_magasin,d=int(r.surface_m2),e=r.type_magasin)
    print(f"   OK dim_magasin : {len(mags)}")
    map_t={r[0]:r[1] for r in conn.run("SELECT date_complete,id_temps FROM dim_temps")}
    map_p={r[0]:r[1] for r in conn.run("SELECT nom_produit,id_produit FROM dim_produit")}
    map_c={(r[0],r[1]):r[2] for r in conn.run("SELECT nom,prenom,id_client FROM dim_client")}
    map_m={r[0]:r[1] for r in conn.run("SELECT nom_magasin,id_magasin FROM dim_magasin")}
    n=0
    for r in df.itertuples():
        it=map_t.get(str(r.date.date())); ip=map_p.get(r.nom_produit)
        ic=map_c.get((r.nom_client,r.prenom_client)); im=map_m.get(r.nom_magasin)
        if all([it,ip,ic,im]):
            conn.run("INSERT INTO fait_ventes (id_temps,id_produit,id_client,id_magasin,quantite,prix_unitaire,remise_pct,montant_ht,montant_ttc,marge) VALUES (:a,:b,:c,:d,:e,:f,:g,:h,:i,:j)",a=it,b=ip,c=ic,d=im,e=int(r.quantite),f=float(r.prix_unitaire),g=float(r.remise_pct),h=float(r.montant_ht),i=float(r.montant_ttc),j=float(r.marge)); n+=1
    print(f"   OK fait_ventes : {n} transactions")
    print("   >>> PostgreSQL charge avec succes!")

if __name__=="__main__":
    print("="*50)
    df_raw=generer_csv("data/ventes_raw.csv")
    df_propre=transformer(df_raw)
    df_propre.to_csv("data/ventes_clean.csv",index=False,encoding="utf-8")
    charger_pg(df_propre)
