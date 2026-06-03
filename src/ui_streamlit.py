from __future__ import annotations

import streamlit as st

from db import connect, fetch_all, init_db, save_feedback
from profile import init_interest_profile, update_profile_from_feedback
from recommender import recommendations, score_articles

RATING_LABELS = {3: "Very interesting", 2: "Somewhat interesting", 1: "Different", 0: "Not useful"}
FEEDBACK_LABELS = ["Technology", "Adoption reason", "Operations", "UX", "Useful for work", "Deep dive", "Near genre but different", "Not interesting", "Clickbait", "Low quality"]


def article_card(article: dict) -> None:
    with st.container(border=True):
        st.subheader(article["title"])
        st.caption(f"{article.get('source_name') or 'unknown'} | {article.get('published_at') or 'date unknown'} | {article.get('recommendation_type') or 'unclassified'}")
        st.write(article.get("summary") or "No summary")
        st.progress(float(article.get("final_score") or 0.0), text=f"score {float(article.get('final_score') or 0.0):.2f}")
        st.write(article.get("recommendation_reason") or "No reason yet")
        st.link_button("Open article", article["url"])
        st.code(article.get("generated_search_terms") or "", language="text")
        with st.form(f"feedback-{article['id']}"):
            rating = st.radio("Rating", options=list(RATING_LABELS.keys()), format_func=lambda value: RATING_LABELS[value], horizontal=True)
            label = st.selectbox("Feedback label", FEEDBACK_LABELS)
            comment = st.text_area("Comment", height=80)
            cols = st.columns(2)
            read_later = cols[0].checkbox("Read later")
            deep_dive = cols[1].checkbox("Deep dive")
            if st.form_submit_button("Save feedback"):
                conn = connect()
                save_feedback(conn, int(article["id"]), int(rating), label, comment, read_later, deep_dive)
                conn.close()
                st.success("Feedback saved")


def main() -> None:
    st.set_page_config(page_title="Serendipity News Engine", layout="wide")
    init_db()
    init_interest_profile()
    st.title("Serendipity News Engine")
    tab_rec, tab_all, tab_profile, tab_feeds, tab_search = st.tabs(["Recommended", "All articles", "Profile", "RSS", "Search terms"])
    with st.sidebar:
        st.header("Actions")
        if st.button("Re-score now"):
            update_profile_from_feedback()
            score_articles()
            st.success("Scored")
    with tab_rec:
        for article in recommendations():
            article_card(article)
    with tab_all:
        conn = connect()
        rows = fetch_all(conn, "SELECT * FROM articles ORDER BY fetched_at DESC LIMIT 200")
        conn.close()
        sources = ["All"] + sorted({row["source_name"] for row in rows if row["source_name"]})
        source = st.selectbox("Source", sources)
        for row in rows:
            item = dict(row)
            if source == "All" or item.get("source_name") == source:
                article_card(item)
    with tab_profile:
        conn = connect()
        profiles = fetch_all(conn, "SELECT profile_name, description, weight, updated_at FROM interest_profile ORDER BY weight DESC")
        pos = fetch_all(conn, "SELECT a.title, f.rating FROM feedback f JOIN articles a ON a.id = f.article_id WHERE f.rating >= 2 ORDER BY f.created_at DESC LIMIT 10")
        neg = fetch_all(conn, "SELECT a.title, f.rating FROM feedback f JOIN articles a ON a.id = f.article_id WHERE f.rating <= 1 ORDER BY f.created_at DESC LIMIT 10")
        conn.close()
        st.dataframe([dict(row) for row in profiles], use_container_width=True)
        st.subheader("Recently positive")
        st.table([dict(row) for row in pos])
        st.subheader("Recently negative")
        st.table([dict(row) for row in neg])
    with tab_feeds:
        st.info("Edit config/feeds.yaml to add, disable, or tune RSS sources.")
    with tab_search:
        conn = connect()
        rows = fetch_all(conn, "SELECT title, generated_search_terms FROM articles WHERE generated_search_terms IS NOT NULL ORDER BY final_score DESC LIMIT 50")
        conn.close()
        st.dataframe([dict(row) for row in rows], use_container_width=True)


if __name__ == "__main__":
    main()
