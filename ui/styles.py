"""Shared visual styling for the Luna Unia Streamlit application."""

import streamlit as st


class LunaStyle:
    """Apply the Luna Unia presentation layer through a scoped API."""

    PALETTE = (
        "--lv-bg:#111111;--lv-surface:rgba(255,255,255,.055);--lv-control:rgba(255,255,255,.07);"
        "--lv-control-hover:rgba(255,255,255,.12);--lv-text:#f5f5f5;--lv-muted:#a3a3a3;"
        "--lv-border:rgba(255,255,255,.14);--lv-strong:rgba(255,255,255,.34);"
        "--lv-accent:#f5f5f5;--lv-soft:rgba(255,255,255,.09);"
        "--lu-running:#4ade80;--lu-degraded:#fbbf24;--lu-offline:#737373;"
        "--luna-text-title:clamp(1.65rem,3vw,2.15rem);--luna-text-subtitle:.78rem;--luna-text-body:.88rem;--luna-text-small:.72rem;"
    )

    @classmethod
    def apply(cls) -> None:
        """Apply the Luna palette, the shared header shell, and the app grid."""
        st.html(f"<style>:root {{{cls.PALETTE}}}</style>")
        st.html(
            """
            <style>
            .stApp { color:var(--lv-text); background:radial-gradient(circle at 82% -10%,rgba(255,255,255,.07),transparent 30rem),var(--lv-bg); }
            .block-container { max-width:1180px; padding-top:2.35rem; padding-bottom:3rem; }
            .stApp p,.stApp label,.stApp [data-testid="stMarkdownContainer"] { color:var(--lv-text); }
            header[data-testid="stHeader"] { background:transparent; }
            #MainMenu,footer,div[data-testid="stDecoration"] { display:none; }
            div[data-testid="stHorizontalBlock"]:has(.lv-header) { align-items:center; margin-bottom:.55rem; }
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button {
                min-height:2.625rem!important; height:2.625rem;
                padding:.45rem .9rem!important;
                border:1px solid var(--lv-border)!important;
                border-radius:.5rem!important;
                background:var(--lv-control)!important;
                color:var(--lv-text)!important;
                box-shadow:0 1px 0 rgba(255,255,255,.03) inset;
                white-space:nowrap;
            }
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button p,
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button span,
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button svg {
                color:var(--lv-text)!important;
                fill:currentColor!important;
                -webkit-text-fill-color:var(--lv-text)!important;
            }
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button:hover {
                border-color:var(--lv-strong)!important;
                background:var(--lv-control-hover)!important;
            }
            div[data-testid="stHorizontalBlock"]:has(.lv-header) .stButton > button[data-testid="stBaseButton-primary"] {
                border-color:var(--lv-strong)!important;
                background:var(--lv-soft)!important;
            }
            .st-key-header_sign_out,.st-key-header_sign_out .stButton { display:flex; justify-content:flex-end; width:7rem!important; min-width:7rem!important; margin-left:auto; }
            .st-key-header_sign_out button { width:7rem!important; min-width:7rem!important; min-height:2.625rem!important; }
            .lv-header { display:flex; align-items:center; gap:1rem; min-height:4.5rem; margin-bottom:1rem; }
            .lv-mark { display:block; flex:0 0 5.75rem; width:5.75rem; height:4.5rem; border:0; border-radius:0; object-fit:contain; object-position:center; box-shadow:none; }
            .lv-title { margin:0; color:var(--lv-text); font-family:inherit; font-size:var(--luna-text-title); font-weight:720; letter-spacing:-.04em; line-height:1; }
            .stApp .lv-subtitle { margin:.32rem 0 0; color:var(--lv-muted); font-size:var(--luna-text-subtitle); font-weight:400; }

            .lu-summary { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:.2rem 0 1.15rem; padding:.75rem 1rem; border:1px solid var(--lv-border); border-radius:.9rem; background:var(--lv-surface); color:var(--lv-muted); font-size:var(--luna-text-small); }
            .stApp .lu-summary strong { color:var(--lv-text); font-size:var(--luna-text-body); font-weight:600; }
            .lu-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
            .stApp a.lu-card,.lu-card {
                display:flex; flex-direction:column; gap:.85rem; min-height:12.5rem; padding:1.1rem;
                border:1px solid var(--lv-border); border-radius:14px; background:var(--lv-surface);
                color:var(--lv-text)!important; text-decoration:none!important;
                box-shadow:0 10px 30px rgba(0,0,0,.12);
                transition:transform 160ms cubic-bezier(.2,.8,.2,1),border-color 140ms ease,background 140ms ease,box-shadow 160ms ease;
            }
            .stApp a.lu-card:hover,.stApp a.lu-card:focus-visible {
                transform:translateY(-4px); border-color:var(--lv-strong); background:var(--lv-control-hover);
                box-shadow:0 18px 32px rgba(0,0,0,.45);
            }
            .stApp a.lu-card:focus-visible { outline:2px solid var(--lv-accent); outline-offset:2px; }
            .lu-card.lu-offline { opacity:.55; cursor:default; box-shadow:none; }
            .lu-card.lu-offline .lu-icon { filter:grayscale(1); }
            .lu-top { display:flex; align-items:center; gap:.85rem; }
            .lu-icon { flex:0 0 3.5rem; width:3.5rem; height:3.5rem; border:1px solid var(--lv-border); border-radius:.8rem; object-fit:cover; }
            .lu-heading { display:flex; flex-direction:column; gap:.3rem; min-width:0; }
            .stApp .lu-name { margin:0; color:var(--lv-text); font-size:1.1rem; font-weight:680; letter-spacing:-.02em; line-height:1.1; }
            .lu-status { display:inline-flex; align-items:center; gap:.4rem; color:var(--lv-muted); font-size:var(--luna-text-small); white-space:nowrap; }
            .lu-status::before { content:""; width:.5rem; height:.5rem; border-radius:999px; background:var(--lu-offline); }
            .lu-running .lu-status::before { background:var(--lu-running); box-shadow:0 0 0 3px rgba(74,222,128,.16); }
            .lu-degraded .lu-status::before { background:var(--lu-degraded); box-shadow:0 0 0 3px rgba(251,191,36,.16); }
            .stApp .lu-desc { flex:1 1 auto; margin:0; color:var(--lv-muted); font-size:var(--luna-text-body); line-height:1.45; }
            .lu-link { display:flex; align-items:center; justify-content:space-between; gap:.5rem; padding-top:.7rem; border-top:1px solid var(--lv-border); color:var(--lv-muted); font-size:var(--luna-text-small); }
            .lu-link span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
            .lu-link svg { flex:0 0 1rem; width:1rem; height:1rem; fill:currentColor; transition:transform 140ms ease; }
            .stApp a.lu-card:hover .lu-link { color:var(--lv-text); }
            .stApp a.lu-card:hover .lu-link svg { transform:translate(2px,-2px); }
            @media (prefers-reduced-motion:reduce) { .stApp a.lu-card,.lu-link svg { transition:none; } .stApp a.lu-card:hover { transform:none; } }

            @media (max-width:1000px) { .lu-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
            @media (max-width:700px) {
                .block-container { padding:.85rem .8rem 2rem; }
                .lv-header { flex-wrap:nowrap!important; gap:.65rem; min-width:0; }
                .lv-header > div { min-width:0; }
                .lv-mark { flex:0 0 4rem; width:4rem; height:3.4rem; }
                .lv-title { white-space:nowrap; font-size:clamp(1.55rem,8vw,1.85rem); }
                .lv-subtitle { display:none; }
                div[data-testid="stHorizontalBlock"]:has(.lv-header) { flex-wrap:wrap!important; }
                div[data-testid="stHorizontalBlock"]:has(.lv-header) > div[data-testid="stColumn"] { flex:1 1 100%!important; width:100%!important; }
                div[data-testid="stHorizontalBlock"] { flex-direction:row!important; flex-wrap:nowrap!important; gap:.5rem!important; }
                div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { min-width:0!important; }
                .st-key-header_sign_out,.st-key-header_sign_out .stButton { width:2.625rem!important; min-width:2.625rem!important; }
                .st-key-header_sign_out button { width:2.625rem!important; min-width:2.625rem!important; padding:0!important; gap:0!important; overflow:hidden!important; }
                .st-key-header_sign_out button p { display:none!important; }
                .st-key-header_sign_out button span[data-testid="stIconMaterial"] { margin:0!important; }
                div[data-testid="stHorizontalBlock"]:has(.st-key-header_sign_out):not(:has(.lv-header)) { flex-wrap:nowrap!important; align-items:center!important; width:100%!important; }
                div[data-testid="stHorizontalBlock"]:has(.st-key-header_sign_out):not(:has(.lv-header)) > div[data-testid="stColumn"]:has(.st-key-refresh_apps) { flex:1 1 0!important; width:auto!important; min-width:0!important; }
                div[data-testid="stHorizontalBlock"]:has(.st-key-header_sign_out):not(:has(.lv-header)) > div[data-testid="stColumn"]:has(.st-key-header_sign_out) { flex:0 0 2.625rem!important; width:2.625rem!important; min-width:2.625rem!important; max-width:2.625rem!important; }
                .lu-grid { grid-template-columns:minmax(0,1fr); gap:.75rem; }
                .lu-card,.stApp a.lu-card { min-height:0; }
                .lu-summary { flex-direction:column; align-items:flex-start; gap:.25rem; }
            }
            </style>
            """
        )
