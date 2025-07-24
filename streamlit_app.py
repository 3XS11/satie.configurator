import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.utils import ImageReader
#V1.28
# Charger les traduction depuis un fichier excel 
@st.cache_data  
def charger_traductions():
    df = pd.read_excel("traductions.xlsx")
    trads = {}
    for _, row in df.iterrows():
        key = row["key"]
        trads[key] = {
            "Français": row.get("FR", key),
            "English": row.get("EN", key),
            "Italiano": row.get("IT", key),
            "Deutsch": row.get("DE", key)
        }
    return trads

# Fonction de traduction
def t(key):
    langue = st.session_state.get("langue", "Français")
    return trads.get(key, {}).get(langue, key)

# choix de langue # SOUS PROGRAMME #

def choix_langue():
    if "langue" not in st.session_state:
        st.session_state.langue = "Français"

    langue = st.session_state.get("langue", "Français")
    st.selectbox("🌐 Langue / Language", ["Français", "English", "Italiano", "Deutsch"], key="langue")  


# Charger et lire base de donée excel avec les réferences # SOUS PROGRAMME #
@st.cache_data
def charger_base():
    return pd.read_excel("base_references.xlsx")


# Configuration des infos clients sur la sidebar # SOUS PROGRAMME #
def infos_clients():

     
    st.sidebar.image("logo.jpg")
    with st.sidebar.expander(t("info_arm_txt"),expanded=False):
        hauteur_armoire = st.number_input(t("hauteur_arm_txt"), 100, 3000, 2000, 100, format="%d", key="hau_arm")
        largeur_armoire = st.number_input(t("largeur_arm_txt"), 100, 2000, 600, 100, format="%d", key="lar_arm")
        marque_armoire = st.text_input(t("marque_arm_txt"), key="marq_arm")
        reference_armoire = st.text_input(t("reference_arm_txt"), key="ref_arm")
    with st.sidebar.expander(t("info_projet_txt"),expanded=False):
        reference_projet = st.text_input(t("reference_projet_txt"), key="ref_projet")
        commentaire_projet = st.text_area(t("commentaire_projet_txt"), key="comm_projet")
        return hauteur_armoire, largeur_armoire
    
    
     

# Section d'ajout des différents profils # SOUS PROGRAMME #
def selection_empillage():
    st.subheader(t("ajouter_empilage_txt"))
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

    type_element = col1.selectbox(t("type_profil_txt"), df_refs["Type"].unique(), key="type_sel")
    ref_options = df_refs[df_refs["Type"] == type_element]["Référence"].dropna().tolist()

    if type_element == "Empty":
       reference = col2.selectbox(t("ref_profil_txt"), ref_options, key="ref_sel_vide")
       hauteur = col3.number_input(t("hauteur_vide_txt"), 1, 1000, step=5, format="%d", key="haut_vide")
    else:
        reference = col2.selectbox(t("ref_profil_txt"), ref_options, key="ref_sel")
        matching = df_refs[(df_refs["Type"] == type_element) & (df_refs["Référence"] == reference)]
        if not matching.empty and "Hauteur (mm)" in matching.columns:
          hauteur = int(matching["Hauteur (mm)"].values[0])
          col3.markdown(f"**{t("hauteur_auto_txt")} :** {hauteur} mm")
        
    if col4.button(t("ajouter_txt")):
      st.session_state.empilage.append({
       "Type": type_element,
       "Référence": reference,
       "Hauteur (mm)": int(hauteur)
        })

# Ajout du tableau d'empillage # SOUS PROGRAMME #
def tableau_empillage(h):
 df_emp = pd.DataFrame(st.session_state.empilage)
 if not df_emp.empty:
    df_emp["Hauteur (mm)"] = df_emp["Hauteur (mm)"].astype(int)
   
    total = df_emp["Hauteur (mm)"].sum()
    hauteur_montant = h - 100
    hauteur_disponible = hauteur_montant - total

    st.markdown(f"### {t('tableau_empilage_txt')}")
    empilage_modifié = st.session_state.empilage.copy()
    changement = False
    st.info(f"{t("hauteur_montant_txt")} : {hauteur_montant} mm")
    st.warning(f"{t("hauteur_dispo_txt")} : {hauteur_disponible} mm") 
 headers = st.columns([1, 2, 2, 2, 1, 1, 2])
 headers[0].markdown(f"**{t('actions_txt')}**")
 headers[1].markdown(f"**{t('type_profil_txt')}**")
 headers[2].markdown(f"**{t('ref_profil_txt')}**")
 headers[3].markdown(f"**{t('hauteur_txt')}**")
 headers[4].markdown(f"**{t('peigne_haut')}**")
 headers[5].markdown(f"**{t('peigne_bas')}**")
 headers[6].markdown(f"**{t('options_txt')}**")

 # Ajout des boutons d'interactions #
 action = None
 index_action = None

 for i, row in enumerate(df_emp.itertuples(index=False, name=None)):
    col_btns, col_type, col_ref, col_haut, col_haut_peigne, col_bas_peigne, col_val = st.columns([1, 2, 2, 2, 1, 1, 2])
    with col_btns:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬆️", key=f"up_{i}") and i > 0:
                action = "up"
                index_action = i
        with col2:
            if st.button("⬇️", key=f"down_{i}") and i < len(empilage_modifié)-1:
                action = "down"
                index_action = i
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                action = "delete"
                index_action = i

    col_type.write(row[0])
    col_ref.write(row[1])
    col_haut.write(f"{row[2]} mm")

    # Initialiser si absent
    if "peigne_haut" not in st.session_state.empilage[i]:
        st.session_state.empilage[i]["peigne_haut"] = True if row[0] in ["PP (flat)", "PPA (DIN rail)"] else False
    if "peigne_bas" not in st.session_state.empilage[i]:
        st.session_state.empilage[i]["peigne_bas"] = True if row[0] in ["PP (flat)", "PPA (DIN rail)"] else False

    # Affichage checkbox si applicable
    if row[0] in ["PP (flat)", "PPA (DIN rail)"]:
        st.session_state.empilage[i]["peigne_haut"] = col_haut_peigne.checkbox("", value=st.session_state.empilage[i]["peigne_haut"], key=f"haut_{i}")
        st.session_state.empilage[i]["peigne_bas"] = col_bas_peigne.checkbox("", value=st.session_state.empilage[i]["peigne_bas"], key=f"bas_{i}")
    else:
        col_haut_peigne.write("-")
        col_bas_peigne.write("-")


    with col_val:
         if st.button(t("option_bouton_txt"), key=f"option_{i}"):
            st.session_state.selected_profil_index = i
                
 # Exécuter l'action sélectionnée après la boucle
 if action == "up" and index_action > 0:
    empilage_modifié[index_action - 1], empilage_modifié[index_action] = empilage_modifié[index_action], empilage_modifié[index_action - 1]
    st.session_state.empilage = empilage_modifié
    st.rerun()
 elif action == "down" and index_action < len(empilage_modifié) - 1:
    empilage_modifié[index_action + 1], empilage_modifié[index_action] = empilage_modifié[index_action], empilage_modifié[index_action + 1]
    st.session_state.empilage = empilage_modifié
    st.rerun()
 elif action == "delete":
    empilage_modifié.pop(index_action)
    st.session_state.empilage = empilage_modifié
    st.rerun()

# Ajout des options selons profils dans la sidebar # SOUS PROGRAMME #
def options_profils():
    index = st.session_state.get("selected_profil_index", None)
    if index is None:
        return

    # Vérifie que l'index est encore valide après suppression
    if index < 0 or index >= len(st.session_state.empilage):
        st.session_state.selected_profil_index = None
        return
    profil = st.session_state.empilage[index]

    st.sidebar.markdown(f"### {t('option_profil_txt')}")
    st.sidebar.write(f"{t("type_profil_txt")} : {profil['Type']}")
    st.sidebar.write(f"{t("ref_profil_txt")} : {profil['Référence']}")
 
    # Initialiser structure si absente
    if "options" not in profil:
        profil["options"] = {}

    # OPTIONS SPÉCIFIQUES : PROFIL PLAT → Rail DIN
    if profil["Type"] == "PP (flat)":
        rail_opts = profil["options"].get("rail_din", {})
        longueur = rail_opts.get("longueur", 50)
        position = rail_opts.get("position", 0)

        with st.sidebar.expander(t("ajout_din"),expanded=False):      
             longueur_input = st.number_input(t("longueur_txt"), 50, 2000, longueur, step=10, key=f"longueur_{index}")
             position_input = st.number_input(t("position_gauche"), 0, 2000, position, step=10, key=f"position_{index}")

             col1, col2 = st.columns(2)
             with col1:
                 if st.button("✅", key=f"valider_option_{index}"):
                    profil["options"]["rail_din"] = {
                             "enabled": True,
                             "longueur": longueur_input,
                             "position": position_input
                         }
                    st.success(t("din_enregistre"))

        with col2:
            if st.button("🗑️", key=f"supprimer_option_{index}"):
                if "rail_din" in profil["options"]:
                    del profil["options"]["rail_din"]
                    st.success(t("din_supprime"))
        
    # OPTIONS PM VERTICALE #
    if profil["Type"] in ["PP (flat)", "PPA (DIN rail)"]:
        pm_opts = profil["options"].get("pm_verticale", {})
        longueur_pm = pm_opts.get("longueur", 100)
        position_pm = pm_opts.get("position", 0)
        entraxe_pm = pm_opts.get("entraxe", 0)

        with st.sidebar.expander(t("ajout_pm"),expanded=False):
             longueur_input = st.number_input(t("longueur_txt"), 20, 2000, longueur_pm, step=10, key=f"pm_len_{index}")
             position_input = st.number_input(t("position_gauche"), 0, 2000, position_pm, step=10, key=f"pm_pos_{index}")
             entraxe_input = st.number_input(t("entraxe_txt"), 0, 2000, entraxe_pm, step=10, key=f"pm_entr_{index}")

             col1, col2 = st.columns(2)
             with col1:
                 if st.button("✅", key=f"valider_pm_{index}"):
                    profil["options"]["pm_verticale"] = {
                     "enabled": True,
                     "longueur": longueur_input,
                     "position": position_input,
                     "entraxe": entraxe_input
                     }
                    st.success(t("pm_enregistre"))

        with col2:
            if st.button("🗑️", key=f"supprimer_pm_{index}"):
               if "pm_verticale" in profil["options"]:
                   del profil["options"]["pm_verticale"]
                   st.success(t("pm_supprime")) 

    

    # OPTION ECROUS DANS PROFILS #

    if profil["Type"] in ["PP (flat)", "PPA (DIN rail)"]:
       with st.sidebar.expander(t("ajout_ecrou"),expanded=False):
            ecrous_opts = profil["options"].get("ecrous", {})

            type_ecrou = ecrous_opts.get("type", "M4")
            quantite = ecrous_opts.get("quantite", 1) 

            type_input = st.selectbox(t("type_ecrou_txt"), ["M4", "M5", "M6", "M8"], index=["M4", "M5", "M6", "M8"].index(type_ecrou), key=f"ecrou_type_{index}")
            quantite_input = st.number_input(t("quantite_txt"), 1, 100, quantite, step=1, key=f"ecrou_qte_{index}")

            col1, col2 = st.columns(2)
            with col1:
                 if st.button("✅", key=f"valider_ecrou_{index}"):
                    profil["options"]["ecrous"] = {
                     "type": type_input,
                     "quantite": quantite_input,
                     "enabled": True
                    }
                    st.success(t("ecrou_enregistre"))
            with col2:
                 if st.button("🗑️", key=f"supprimer_ecrou_{index}"):
                    if "ecrous" in profil["options"]:
                        del profil["options"]["ecrous"]
                        st.success(t("ecrou_supprime"))

    # COMMENTAIRES CLIENTS #

    st.sidebar.markdown(t("commentaire_txt"))
    commentaire = profil.get("commentaire", "")

    nouveau_commentaire = st.sidebar.text_area(t("ajout_commentaire"), commentaire, key=f"commentaire_{index}")

    # Sauvegarde si modifié
    if nouveau_commentaire != commentaire:
        profil["commentaire"] = nouveau_commentaire
   

# Affichage d'un visuel châssis # SOUS PROGRAMME #
def visuel_chassis(h, la, show=True):
    

    fig_width_inch = 6
    fig_height_inch = 10
    fig, ax = plt.subplots(figsize=(fig_width_inch, fig_height_inch)) 

    #définir l'échelle mm en pouces
    largeur_profil = la -100 #largeur réel du châssis
    mm_to_inch = 1 / 24.4 

    ax.set_xlim(0, la)
    ax.set_ylim(0, la)
    ax.invert_yaxis()  # Pour que le haut du châssis soit en haut du dessin

    current_y = 0 #point de départ du haut
    couleurs_type = {
        "PPA (DIN rail)": "#babab6",
        "peigne": "#87CEFA",
        "CPF": "#287FFA",
        "Empty": "#fcfcfc",
        "PP (flat)": "#babab6"
    }
    
    st.markdown(f"### {t('apercu_chassis')}")
    
    # CREATION AXE VISUEL #
    fig, ax = plt.subplots(figsize=(fig_width_inch, fig_height_inch))

    # Zone de tracé en mm
    ax.set_xlim(-50, la + 50)  # Laisse un peu de marge à gauche pour la graduation
    ax.set_ylim(0, h)
    ax.invert_yaxis()

    # Affichage de l’échelle verticale tous les 100 mm
    graduation_interval = 100
    for y in range(0, h , graduation_interval):
     ax.hlines(y, -5, -30, color='black', linewidth=0.3)
     ax.text(-50, y, f"{y} mm", va='center', ha='right', fontsize=5)

    # FIN CREATION AXE VISUEL #



     # --- MONTANTS VERTICAUX GAUCHE ET DROITE ---
    largeur_montant = 30  # en mm
    hauteur_montant = h - 100  # comme dans le calcul global

     # Montant gauche
    ax.add_patch(patches.Rectangle(
    (0, 0),
    largeur_montant,
    hauteur_montant,
    facecolor="#888888", edgecolor="black", linewidth=0.5,
    zorder=1
    ))

    # Montant droit
    ax.add_patch(patches.Rectangle(
    ((la - 70 - largeur_montant) - largeur_montant, 0),
    largeur_montant,
    hauteur_montant,
    facecolor="#888888", edgecolor="black", linewidth=0.5,
    zorder=1
    ))

    
    for elt in st.session_state.empilage:
        hauteur = elt["Hauteur (mm)"]
        type_elt = elt["Type"]
        color = couleurs_type.get(type_elt, "#CCCCCC")

        peigne_haut = elt.get("peigne_haut", True)
        peigne_bas = elt.get("peigne_bas", True)
        peigne_height = 15  # mm visuel utilisé pour ajuster les positions

        # Si peigne haut : décaler vers le bas
        if peigne_haut:
           current_y += peigne_height


        # Profil
        zorder=0 if type_elt == "Empty" else 2
        linewidth=0 if type_elt =="Empty" else 0.3
        rect = patches.Rectangle((0, current_y), largeur_profil, hauteur, facecolor=color, edgecolor='black', linewidth=linewidth, zorder=zorder)
        ax.add_patch(rect)
        ax.text(la + 10, current_y + hauteur / 2, elt["Référence"], va='center', fontsize=6)
        

        # AFFICHAGE DES RAINURE PROFILS #
          
        if type_elt in ["PP (flat)", "PPA (DIN rail)"]:
           # Aller chercher les rainures depuis la base Excel
           reference = elt["Référence"]
           rainure_info = df_refs[df_refs["Référence"] == reference]
    
           if not rainure_info.empty and "Rainures Y (mm)" in rainure_info.columns:
               val = rainure_info.iloc[0]["Rainures Y (mm)"]
               if pd.notna(val):
                   try:
                       positions = [float(y.strip()) for y in str(val).split(";") if y.strip()]
                       for y_rel in positions:
                           y_line = current_y + y_rel
                           ax.hlines(
                               y=y_line,
                               xmin=0,  # ou 50 si tu veux à l'intérieur du châssis
                               xmax=largeur_profil,
                               color='black',
                               linewidth=0.2,
                              
                            )
                   except:
                         pass

        # --- PEIGNES ---
        if type_elt in ["PP (flat)", "PPA (DIN rail)"]:
            largeur_peigne = largeur_profil
            hauteur_peigne = 15  # visuel
            x_peigne = 0

            if peigne_haut:
                y_haut = current_y
                ax.add_patch(patches.Rectangle(
                    (x_peigne, y_haut - hauteur_peigne),
                    largeur_peigne,
                    hauteur_peigne,
                    facecolor=couleurs_type.get("peigne"),
                    edgecolor='black',
                    linewidth=0.2
                ))
                ax.text(
                    la + 10,
                    y_haut - hauteur_peigne / 2,
                    "PF300",
                    ha="left",
                    va="center",
                    fontsize=5
                )

            if peigne_bas:
                y_bas = current_y + hauteur
                ax.add_patch(patches.Rectangle(
                    (x_peigne, y_bas),
                    largeur_peigne,
                    hauteur_peigne,
                    facecolor=couleurs_type.get("peigne"),
                    edgecolor='black',
                    linewidth=0.2
                ))
                ax.text(
                    la + 10,
                    y_bas + hauteur_peigne / 2,
                    "PF300",
                    ha="left",
                    va="center",
                    fontsize=5
                )




        # AFFICHAGE PM #
        pm = elt.get("options", {}).get("pm_verticale", None)
        if pm and pm.get("enabled"):
           largeur_pm = 38  # mm
           hauteur_pm = pm.get("longueur", 100)  # mm
           position_x = pm.get("position", 0)
           entraxe = pm.get("entraxe", 0)

           y_top = current_y  # point haut du profil actuel

           for offset in [0, entraxe] if entraxe > 0 else [0]:
               x_left = position_x + offset
               ax.add_patch(patches.Rectangle(
                   (x_left, y_top),
                   largeur_pm,
                   hauteur_pm,
                   facecolor="grey",
                   edgecolor="black",
                   linewidth=0.3,
                   zorder=10  
               ))

        


        # Rail DIN (si présent)
        rail = elt.get("options", {}).get("rail_din", None)
        if rail and rail.get("enabled"):
            rail_x = rail["position"]
            rail_width = rail["longueur"]
            rail_height = 35
            rail_y = current_y + hauteur / 2 - rail_height / 2

            ax.add_patch(patches.Rectangle(
                (rail_x, rail_y),
                rail_width,
                rail_height,
                facecolor='gray',
                edgecolor='black',
                linewidth=0.3,
                zorder = 8
            ))
            ax.text(rail_x + rail_width / 2, rail_y + rail_height / 2,
                    "DIN35", ha="center", va="center", fontsize=6, zorder = 10)


            

            # Écrous (si présents)
        ecrou = elt.get("options", {}).get("ecrous", None)
        if ecrou:
            couleur_ecrou = {
                "M4": "green",
                "M5": "blue",
                "M6": "red",
                "M8": "black"
            }.get(ecrou.get("type"), "gray")

            nb = ecrou.get("quantite", 0)
            ecrou_size = 17
            ecart = 25

            total_width = (nb - 1) * ecart
            start_x = (largeur_profil - total_width) / 2
            y_ecrou = current_y + hauteur / 2 - ecrou_size / 2

            for i in range(nb):
                x_ecrou = start_x + i * ecart
                ax.add_patch(patches.Rectangle(
                    (x_ecrou, y_ecrou),
                    ecrou_size,
                    ecrou_size,
                    facecolor=couleur_ecrou,
                    edgecolor='black',
                    linewidth=0.3,
                    zorder = 9
                ))

  

    
       
        # Décalage vertical pour l’élément suivant
        current_y += hauteur 
        if peigne_bas:
            current_y += peigne_height

    ax.set_aspect('equal')
    ax.axis("off")
    if show:
        st.pyplot(fig)
    else:
        return fig



# Generer le visuel au format image # SOUS PROGRAMME #
def generer_visuel_image(h, la):
    buf = BytesIO()
    fig = visuel_chassis(h, la, show=False)  # Tu dois modifier ta fonction pour accepter show=False
    fig.savefig(buf, format='PNG', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf




# Generer le PDF récapitulatif # SOUS PROGRAMME #
def generer_pdf(empilage,):
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    logo_path = ("logo.jpg")
    logo = ImageReader(logo_path)
    c.drawImage(logo, x=425, y=752, width=150, height=100, preserveAspectRatio=True, mask='auto')

    y = height - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, t("recap_projet_txt"))
    y -= 30


    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"{t("reference_projet_txt")} : {st.session_state.get('ref_projet', '—')}")
    y -= 30
    c.drawString(40, y, f"{t("commentaire_projet_txt")} : {st.session_state.get('comm_projet', '—')}")
    y -= 30
    c.drawString(40, y, f"{t("marque_arm_txt")} : {st.session_state.get('marq_arm', '—')}")
    y -= 30
    c.drawString(40, y, f"{t("reference_arm_txt")} : {st.session_state.get('ref_arm', '—')}")
    y -= 30
    c.drawString(40, y, f"{t("hauteur_de_armoire_txt")} : {st.session_state.get('hau_arm', '—')}")
    y -= 30
    c.drawString(40, y, f"{t("largeur_de_armoire_txt")} : {st.session_state.get('lar_arm', '—')}")

    # Inserer image du visuel #
   
    img_buffer = generer_visuel_image(h, la)
    image = ImageReader(img_buffer)
    iw, ih = image.getSize()
    # ratio de redimensionnement
    max_width = 250
    scale = max_width / iw
    new_height = ih * scale

    c.drawImage(image, x=40, y=0, width=max_width, height=new_height)


    c.showPage() #page suivante #
    c.drawImage(logo, x=425, y=752, width=150, height=100, preserveAspectRatio=True, mask='auto')
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, t("tableau_empilage_txt"))
    y = 770
    for i, elt in enumerate(empilage):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"{i+1}. {elt['Référence']} - {elt['Hauteur (mm)']} mm")
        y -= 15
        c.setFont("Helvetica", 10)

        options = elt.get("options", {})
        commentaires = elt.get("commentaire", "")
        
        if "peigne_haut" in elt and elt["peigne_haut"]:
            c.drawString(60, y, f"- {t("peigne_haut_active")}")
            y -= 15
        if "peigne_bas" in elt and elt["peigne_bas"]:
            c.drawString(60, y, f"- {t("peigne_bas_active")}")
            y -= 15
        if "rail_din" in options:
            rail = options["rail_din"]
            c.drawString(60, y, f"- {t("rail_din_txt")} : {rail['longueur']} mm - {rail['position']} mm {t("bord_gauche")}")
            y -= 15
        if "ecrous" in options:
            ec = options["ecrous"]
            c.drawString(60, y, f"- {t("ecrous_txt")} : {ec['type']} x{ec['quantite']}")
            y -= 15
        if "pm_verticale" in options:
            pm = options["pm_verticale"]
            c.drawString(60, y, f"- PM38 : {pm['longueur']} mm - {pm['position']} mm {t("bord_gauche")} - {t("entraxe_seul_txt")} : {pm['entraxe']}")
            y -= 15


        if commentaires:
            c.drawString(60, y, f"- {t("commentaire_seul_txt")} : {commentaires}")
            y -= 15

        y -= 10
        if y < 60:
            c.showPage()
            y = height - 40

    c.save()
    buffer.seek(0)
    return buffer







    

######## Programme principale MAIN #########

trads = charger_traductions()

choix_langue()

# Configuration du haut de page #

st.set_page_config(page_title="Configurateur Châssis", layout="wide")
st.title(t("titre_application"))


# Charger et lire base de donée excel avec les réferences #

df_refs = charger_base()
if "empilage" not in st.session_state:
    st.session_state.empilage = []


selection_empillage()

h,la = infos_clients()   

tableau_empillage(h)

options_profils()

visuel_chassis(h,la)


pdf_buffer = generer_pdf(
    st.session_state.empilage,
   
)

st.download_button(
    label=(t("telecharger_pdf_txt")),
    data=pdf_buffer,
    file_name="recapitulatif_chassis.pdf",
    mime="application/pdf"
)


