from __future__ import annotations

import streamlit as st

from src.db import connect, fetch_all, init_db, save_feedback
from src.profile import init_interest_profile, update_profile_from_feedback
from src.recommender import recommendations, score_articles

RATING_LABELS = {3: "とても面白い", 2: "少し気になる", 1: "方向が違う", 0: "不要"}
FEEDBACK_LABELS = [
    "技術が面白い",
    "普及しない理由が面白い",
    "制度・運用が面白い",
    "UXが面白い",
    "自分の作業に使えそう",
    "深掘りしたい",
    "ジャンルは近いが内容は違う",
    "興味がない",
    "釣りタイトル",
    "情報が薄い",
]
TYPE_LABELS = {
    "known_interest": "既知の関心",
    "adjacent_interest": "隣接する関心",
    "surprise": "意外性",
    "general": "総合候補",
}
PROFILE_COLUMNS = {
    "profile_name": "関心軸",
    "description": "説明",
    "weight": "重み",
    "updated_at": "更新日時",
}
FEEDBACK_COLUMNS = {
    "title": "記事タイトル",
    "rating": "評価",
}
SEARCH_COLUMNS = {
    "title": "記事タイトル",
    "generated_search_terms": "検索語候補",
}


def article_card(article: dict) -> None:
    with st.container(border=True):
        st.subheader(article["title"])
        recommendation_type = article.get("recommendation_type") or "general"
        st.caption(f"{article.get('source_name') or '情報源不明'} | {article.get('published_at') or '日付不明'} | {TYPE_LABELS.get(recommendation_type, recommendation_type)}")
        st.write(article.get("summary") or "概要なし")
        st.progress(float(article.get("final_score") or 0.0), text=f"スコア {float(article.get('final_score') or 0.0):.2f}")
        st.write(article.get("recommendation_reason") or "推薦理由はまだありません。")
        st.link_button("記事を開く", article["url"])
        st.caption("次回検索用キーワード候補")
        st.code(article.get("generated_search_terms") or "", language="text")
        with st.form(f"feedback-{article['id']}"):
            rating = st.radio("評価", options=list(RATING_LABELS.keys()), format_func=lambda value: RATING_LABELS[value], horizontal=True)
            label = st.selectbox("フィードバック分類", FEEDBACK_LABELS)
            comment = st.text_area("コメント", height=80)
            cols = st.columns(2)
            read_later = cols[0].checkbox("あとで読む")
            deep_dive = cols[1].checkbox("深掘り")
            if st.form_submit_button("フィードバックを保存"):
                conn = connect()
                save_feedback(conn, int(article["id"]), int(rating), label, comment, read_later, deep_dive)
                conn.close()
                st.success("フィードバックを保存しました")


def main() -> None:
    st.set_page_config(page_title="セレンディピティ記事推薦", layout="wide")
    init_db()
    init_interest_profile()
    st.title("セレンディピティ記事推薦")
    tab_rec, tab_all, tab_profile, tab_feeds, tab_search = st.tabs(["推薦記事", "全記事", "関心プロファイル", "RSS設定", "検索語候補"])
    with st.sidebar:
        st.header("操作")
        if st.button("今すぐ再スコアリング"):
            update_profile_from_feedback()
            score_articles()
            st.success("スコアを再計算しました")
    with tab_rec:
        for article in recommendations():
            article_card(article)
    with tab_all:
        conn = connect()
        rows = fetch_all(conn, "SELECT * FROM articles ORDER BY fetched_at DESC LIMIT 200")
        conn.close()
        sources = ["すべて"] + sorted({row["source_name"] for row in rows if row["source_name"]})
        source = st.selectbox("情報源", sources)
        for row in rows:
            item = dict(row)
            if source == "すべて" or item.get("source_name") == source:
                article_card(item)
    with tab_profile:
        conn = connect()
        profiles = fetch_all(conn, "SELECT profile_name, description, weight, updated_at FROM interest_profile ORDER BY weight DESC")
        pos = fetch_all(conn, "SELECT a.title, f.rating FROM feedback f JOIN articles a ON a.id = f.article_id WHERE f.rating >= 2 ORDER BY f.created_at DESC LIMIT 10")
        neg = fetch_all(conn, "SELECT a.title, f.rating FROM feedback f JOIN articles a ON a.id = f.article_id WHERE f.rating <= 1 ORDER BY f.created_at DESC LIMIT 10")
        conn.close()
        st.dataframe([dict(row) for row in profiles], use_container_width=True, column_config=PROFILE_COLUMNS)
        st.subheader("最近の高評価")
        st.dataframe([dict(row) for row in pos], use_container_width=True, column_config=FEEDBACK_COLUMNS, hide_index=True)
        st.subheader("最近の低評価")
        st.dataframe([dict(row) for row in neg], use_container_width=True, column_config=FEEDBACK_COLUMNS, hide_index=True)
    with tab_feeds:
        st.info("RSS の追加、無効化、信頼度調整は config/feeds.yaml を編集してください。")
    with tab_search:
        conn = connect()
        rows = fetch_all(conn, "SELECT title, generated_search_terms FROM articles WHERE generated_search_terms IS NOT NULL ORDER BY final_score DESC LIMIT 50")
        conn.close()
        st.dataframe([dict(row) for row in rows], use_container_width=True, column_config=SEARCH_COLUMNS, hide_index=True)


if __name__ == "__main__":
    main()
