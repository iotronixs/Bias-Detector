import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import os

DATA_FILE = "database.xlsx"

# --- Helper functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        data = pd.read_excel(DATA_FILE)
    else:
        data = pd.DataFrame(columns=["Sentence", "Bias"])
        data.to_excel(DATA_FILE, index=False)
    return data


def train_model(data):
    if len(data) < 2:
        sentences = ["This is neutral.", "This is biased!"]
        labels = [0, 1]
    else:
        sentences = data["Sentence"].astype(str).tolist()
        labels = data["Bias"].astype(int).tolist()

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(sentences)
    model = LogisticRegression()
    model.fit(X, labels)
    return model, vectorizer


# --- Initialize session state ---
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "model" not in st.session_state or "vectorizer" not in st.session_state:
    st.session_state.model, st.session_state.vectorizer = train_model(st.session_state.data)
if "last_sentence" not in st.session_state:
    st.session_state.last_sentence = None
if "last_pred" not in st.session_state:
    st.session_state.last_pred = None

# --- Streamlit UI ---
st.set_page_config(page_title="Bias Detector", layout="wide")
st.title("🧠 Bias Detector")

# Layout: two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Input Text")
    text = st.text_area("Enter a sentence here...", height=150)

    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
    check_pressed = col_btn1.button("Check Bias")
    correct_pressed = col_btn2.button("Correct ✅")
    incorrect_pressed = col_btn3.button("Incorrect ❌")
    retrain_pressed = col_btn4.button("Retrain Model 🔁")

    if check_pressed:
        if not text.strip():
            st.warning("Please enter a sentence.")
        else:
            X_input = st.session_state.vectorizer.transform([text])
            pred = st.session_state.model.predict(X_input)[0]
            prob = st.session_state.model.predict_proba(X_input)[0][pred]
            st.session_state.last_sentence = text
            st.session_state.last_pred = pred

            label = "Biased ❌" if pred == 1 else "Neutral ✅"
            st.markdown(f"### Prediction: {label} ({prob*100:.2f}%)")
            st.progress(prob)

    if correct_pressed:
        if st.session_state.last_sentence is not None:
            df = load_data()
            df.loc[len(df)] = [st.session_state.last_sentence, st.session_state.last_pred]
            df.to_excel(DATA_FILE, index=False)
            st.session_state.data = df
            st.success("✔️ Added as correct to dataset.")
        else:
            st.warning("No previous prediction found.")

    if incorrect_pressed:
        if st.session_state.last_sentence is not None:
            corrected_label = 0 if st.session_state.last_pred == 1 else 1
            df = load_data()
            df.loc[len(df)] = [st.session_state.last_sentence, corrected_label]
            df.to_excel(DATA_FILE, index=False)
            st.session_state.data = df
            st.success("❌ Added as incorrect (corrected label).")
        else:
            st.warning("No previous prediction found.")

    if retrain_pressed:
        st.session_state.model, st.session_state.vectorizer = train_model(st.session_state.data)
        st.success("🔁 Model retrained successfully!")


with col2:
    st.subheader("📊 Dataset Summary")

    df = st.session_state.data
    total = len(df)
    biased = (df["Bias"] == 1).sum() if total > 0 else 0
    neutral = (df["Bias"] == 0).sum() if total > 0 else 0

    st.write(f"**Total entries:** {total}")
    st.write(f"**Neutral statements:** {neutral}")
    st.write(f"**Biased statements:** {biased}")

    if total > 0:
        st.markdown("#### Last 5 Entries")
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.info("Database is empty. Start by checking a sentence!")

