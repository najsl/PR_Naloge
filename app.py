import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

#streamlit run app.py

st.set_page_config(page_title="MovieLens Analiza", layout="wide")

@st.cache_data
def load_data():
    movies = pd.read_csv("podatki/ml-latest-small/movies.csv")
    ratings = pd.read_csv("podatki/ml-latest-small/ratings.csv")
    return movies, ratings

movies, ratings = load_data()

movies['leto'] = movies['title'].str.extract(r'\((\d{4})\)').astype(float)

menu = st.sidebar.radio(
    "Izberi stran", 
    ["1. Analiza podatkov", "2. Primerjava dveh filmov", "3. Priporočilni sistem"]
)

# 1. naloga
if menu == "1. Analiza podatkov":
    st.title("Analiza podatkov")
    st.write("Izpiši 10 filmov z najboljšo povprečno oceno, s filtri po žanru, letu in minimalnem številu ocen.")

    ratings_grouped = ratings.groupby("movieId").agg(
        povprecje=("rating", "mean"),
        st_ocen=("rating", "count")
    ).reset_index()
    merged = pd.merge(movies, ratings_grouped, on="movieId")

    min_ocen = st.slider("Minimalno število ocen", 1, 100, 10)
    vsi_letniki = sorted(merged["leto"].dropna().astype(int).unique())
    leto = st.selectbox("Leto izida filma (opcijsko)", [None] + vsi_letniki)
    vsi_zanri = sorted(set(z for zz in merged["genres"].str.split("|") for z in zz))
    zanr = st.selectbox("Žanr (opcijsko)", [None] + vsi_zanri)

    filt = merged["st_ocen"] >= min_ocen
    if leto:
        filt &= merged["leto"] == leto
    if zanr:
        filt &= merged["genres"].str.contains(zanr)

    rez = merged[filt].sort_values("povprecje", ascending=False).head(10)
    st.write("10 filmov z najboljšo povprečno oceno (upoštevani filtri):")
    st.dataframe(rez[["title", "povprecje", "st_ocen", "genres", "leto"]])

# 2. naloga
elif menu == "2. Primerjava dveh filmov":
    st.title("Primerjava dveh filmov")
    st.write("Primerjaj dva filma: povprečna ocena, število ocen, histogram in trend po letih.")

    film_choices = movies["title"].tolist()
    film1 = st.selectbox("Izberi prvi film", film_choices, index=0)
    film2 = st.selectbox("Izberi drugi film", film_choices, index=1)

    id1 = movies.loc[movies['title'] == film1, 'movieId'].values[0]
    id2 = movies.loc[movies['title'] == film2, 'movieId'].values[0]

    r1 = ratings[ratings["movieId"] == id1]
    r2 = ratings[ratings["movieId"] == id2]

    def film_stat(ratings):
        return {
            "Povprečna ocena": round(ratings["rating"].mean(), 2),
            "Število ocen": int(ratings["rating"].count()),
            "Std. odklon": round(ratings["rating"].std(), 2)
        }

    st.subheader("Statistika")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{film1}**")
        st.write(film_stat(r1))
    with col2:
        st.write(f"**{film2}**")
        st.write(film_stat(r2))

    st.subheader("Histogram ocen")
    fig, axs = plt.subplots(1, 2, figsize=(10,4))
    axs[0].hist(r1["rating"], bins=[0.5,1.5,2.5,3.5,4.5,5.5], rwidth=0.8)
    axs[0].set_title(film1)
    axs[0].set_xlabel("Ocena")
    axs[0].set_ylabel("Št. ocen")
    axs[1].hist(r2["rating"], bins=[0.5,1.5,2.5,3.5,4.5,5.5], rwidth=0.8)
    axs[1].set_title(film2)
    axs[1].set_xlabel("Ocena")
    st.pyplot(fig)

    st.subheader("Povprečna letna ocena")

    ratings['leto_'] = pd.to_datetime(ratings['timestamp'], unit='s').dt.year
    povp_leta_1 = r1.groupby(r1['timestamp'].map(lambda x: pd.to_datetime(x, unit='s').year))["rating"].mean()
    povp_leta_2 = r2.groupby(r2['timestamp'].map(lambda x: pd.to_datetime(x, unit='s').year))["rating"].mean()

    fig2, ax = plt.subplots()
    ax.plot(povp_leta_1.index, povp_leta_1.values, marker='o', label=film1)
    ax.plot(povp_leta_2.index, povp_leta_2.values, marker='o', label=film2)
    ax.set_xlabel("Leto")
    ax.set_ylabel("Povprečna ocena")
    ax.set_title("Povprečna letna ocena")
    ax.legend()
    st.pyplot(fig2)

    st.subheader("Število ocen na leto")
    count_leta_1 = r1.groupby(r1['timestamp'].map(lambda x: pd.to_datetime(x, unit='s').year))["rating"].count()
    count_leta_2 = r2.groupby(r2['timestamp'].map(lambda x: pd.to_datetime(x, unit='s').year))["rating"].count()

    fig3, ax = plt.subplots()
    ax.bar(count_leta_1.index - 0.2, count_leta_1.values, width=0.4, label=film1)
    ax.bar(count_leta_2.index + 0.2, count_leta_2.values, width=0.4, label=film2)
    ax.set_xlabel("Leto")
    ax.set_ylabel("Št. ocen")
    ax.set_title("Število ocen na leto")
    ax.legend()
    st.pyplot(fig3)

    # 3. naloga
if menu == "3. Priporočilni sistem":
    st.title("Priporočilni sistem")
    st.write("Prijava in registracija za ocenjevanje filmov ter priporočila na podlagi ocen.")

    # Preprosta shramba uporabnikov in ocen (za demo namen je vse le v seji)
    if "users" not in st.session_state:
        st.session_state.users = {}  # {username: password}
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "user_ratings" not in st.session_state:
        st.session_state.user_ratings = {}  # {username: {movieId: rating}}

    # Prikaz ustreznega obrazca (login / register)
    login_tab, register_tab = st.tabs(["Prijava", "Registracija"])
    with login_tab:
        st.subheader("Prijava")
        username = st.text_input("Uporabniško ime", key="login_user")
        password = st.text_input("Geslo", type="password", key="login_pass")
        if st.button("Prijava"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.current_user = username
                st.success(f"Pozdravljen, {username}!")
            else:
                st.error("Napačno uporabniško ime ali geslo.")
    with register_tab:
        st.subheader("Registracija")
        reg_username = st.text_input("Novo uporabniško ime", key="reg_user")
        reg_password = st.text_input("Novo geslo", type="password", key="reg_pass")
        if st.button("Registriraj se"):
            if reg_username in st.session_state.users:
                st.error("Uporabniško ime že obstaja.")
            elif not reg_username or not reg_password:
                st.error("Vpiši uporabniško ime in geslo.")
            else:
                st.session_state.users[reg_username] = reg_password
                st.session_state.user_ratings[reg_username] = {}
                st.success("Registracija uspešna! Sedaj se prijavi.")

    # Če je uporabnik prijavljen
    if st.session_state.current_user:
        st.success(f"Prijavljen kot: {st.session_state.current_user}")
        # Ocenjevanje filmov
        st.write("Ocenjevanje filmov (1-5):")
        all_titles = movies["title"].tolist()
        oceni_film = st.selectbox("Izberi film za oceno", all_titles)
        movie_id = movies[movies["title"] == oceni_film]["movieId"].values[0]
        ocena = st.slider("Tvoja ocena", 1, 5, 3)
        if st.button("Shrani oceno"):
            user = st.session_state.current_user
            if user not in st.session_state.user_ratings:
                st.session_state.user_ratings[user] = {}
            st.session_state.user_ratings[user][movie_id] = ocena
            st.success("Ocena shranjena!")

        # Prikaz dosedanjih ocen
        user_ratings = st.session_state.user_ratings.get(st.session_state.current_user, {})
        if user_ratings:
            df_ratings = pd.DataFrame([
                {
                    "title": movies[movies["movieId"] == int(mid)]["title"].values[0],
                    "ocena": user_ratings[mid]
                } for mid in user_ratings
            ])
            st.write("Tvoje ocene:")
            st.dataframe(df_ratings)

        # Priporočila, če je vsaj 10 ocen
        if len(user_ratings) >= 10:
            st.success("Ker si ocenil vsaj 10 filmov, tukaj je 10 priporočil:")
            ocenjeni = set(map(int, user_ratings.keys()))
            ratings_grouped = ratings.groupby("movieId").agg(
                povprecje=("rating", "mean"),
                st_ocen=("rating", "count")
            ).reset_index()
            merged = pd.merge(movies, ratings_grouped, on="movieId")
            kandidati = merged[~merged["movieId"].isin(ocenjeni)]
            priporocila = kandidati.sort_values(
                ["povprecje", "st_ocen"], ascending=[False, False]
            ).head(10)
            st.dataframe(priporocila[["title", "povprecje", "st_ocen", "genres"]])
        else:
            st.info(f"Za priporočila oceni še {10 - len(user_ratings)} filmov.")
    else:
        st.warning("Za ocenjevanje in priporočila se najprej prijavi.")
