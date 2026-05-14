import sqlite3, numpy as np, pandas as pd, matplotlib.pyplot as plt, warnings
warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DB_PATH = "data/datawarehouse.db"

def extraire():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT t.mois, t.trimestre, t.annee, t.est_weekend,
               p.categorie, p.prix_unitaire,
               c.age, c.genre, c.segment,
               m.region, m.surface_m2, m.type_magasin,
               f.quantite, f.remise_pct, f.montant_ttc AS cible
        FROM fait_ventes f
        JOIN dim_temps t ON f.id_temps=t.id_temps
        JOIN dim_produit p ON f.id_produit=p.id_produit
        JOIN dim_client c ON f.id_client=c.id_client
        JOIN dim_magasin m ON f.id_magasin=m.id_magasin
    """, conn)
    conn.close()
    print(f"   OK : {len(df)} lignes extraites du DW")
    return df

def preparer(df):
    for col in ["categorie","genre","segment","region","type_magasin"]:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))
    X = df.drop(columns=["cible"])
    y = df["cible"]
    X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)
    print(f"   OK : train={len(X_train)} / test={len(X_test)}")
    return X_train,X_test,y_train,y_test,X.columns.tolist()

def entrainer(X_train,y_train):
    m = RandomForestRegressor(n_estimators=200,max_depth=12,random_state=42,n_jobs=-1)
    m.fit(X_train,y_train)
    print("   OK : modele entraine (200 arbres)")
    return m

def evaluer(m,X_test,y_test):
    y_pred = m.predict(X_test)
    mae=mean_absolute_error(y_test,y_pred)
    rmse=np.sqrt(mean_squared_error(y_test,y_pred))
    r2=r2_score(y_test,y_pred)
    print(f"   MAE  : {mae:.2f} euros")
    print(f"   RMSE : {rmse:.2f} euros")
    print(f"   R2   : {r2:.4f}  ({r2*100:.1f}% variance expliquee)")
    return y_pred,{"MAE":mae,"RMSE":rmse,"R2":r2}

def visualiser(m,y_test,y_pred,features,metriques):
    fig,axes=plt.subplots(2,2,figsize=(14,10))
    fig.suptitle("Modele IA sur Data Warehouse - M1",fontsize=15,fontweight="bold")
    # 1 - Feature importance
    imp=pd.Series(m.feature_importances_,index=features).sort_values()
    imp.plot(kind="barh",ax=axes[0,0],color="#1565C0"); axes[0,0].set_title("Importance des Features"); axes[0,0].spines[["top","right"]].set_visible(False)
    # 2 - Reel vs Predit
    axes[0,1].scatter(y_test,y_pred,alpha=0.3,color="#1565C0",s=15)
    lim=max(y_test.max(),y_pred.max())
    axes[0,1].plot([0,lim],[0,lim],color="red",lw=1.5,linestyle="--")
    axes[0,1].set_title(f"Reel vs Predit  (R2={metriques['R2']:.3f})")
    axes[0,1].set_xlabel("Reel (euros)"); axes[0,1].set_ylabel("Predit (euros)")
    axes[0,1].spines[["top","right"]].set_visible(False)
    # 3 - Residus
    residus=y_test.values-y_pred
    axes[1,0].hist(residus,bins=40,color="#1565C0",edgecolor="white",alpha=0.85)
    axes[1,0].axvline(0,color="red",lw=2,linestyle="--")
    axes[1,0].set_title("Distribution des Residus"); axes[1,0].set_xlabel("Erreur (euros)")
    axes[1,0].spines[["top","right"]].set_visible(False)
    # 4 - Metriques
    axes[1,1].axis("off")
    data=[["MAE",f"{metriques['MAE']:.2f} euros"],["RMSE",f"{metriques['RMSE']:.2f} euros"],["R2",f"{metriques['R2']:.4f}"],["Train","3 999 lignes"],["Test","1 000 lignes"],["Algo","Random Forest 200 arbres"]]
    t=axes[1,1].table(cellText=data,colLabels=["Metrique","Valeur"],loc="center",cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(11); t.scale(1,2)
    for (row,col),cell in t.get_celld().items():
        if row==0: cell.set_facecolor("#1565C0"); cell.set_text_props(color="white",fontweight="bold")
        elif row%2==0: cell.set_facecolor("#E3F2FD")
        cell.set_edgecolor("white")
    axes[1,1].set_title("Resume du Modele")
    plt.tight_layout()
    plt.savefig("data/resultats_ml.png",dpi=150,bbox_inches="tight",facecolor="white")
    print("   OK : graphiques -> data/resultats_ml.png")
    plt.show()

if __name__=="__main__":
    print("="*50)
    print("  MODELE IA - M1 Intelligence Artificielle & DW")
    print("="*50)
    df=extraire()
    X_train,X_test,y_train,y_test,features=preparer(df)
    modele=entrainer(X_train,y_train)
    y_pred,metriques=evaluer(modele,X_test,y_test)
    visualiser(modele,y_test,y_pred,features,metriques)
    print("\n>>> Partie pratique terminee avec succes !")
