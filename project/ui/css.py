custom_css = """
    /* ============================================
       DARK PALETTE (pinned)
       ============================================
       This UI is dark by design, but Gradio picks its palette from the
       visitor's OS / browser theme. With a light-mode browser the theme text
       colour stayed dark (--body-text-color: #27272a) while this stylesheet
       forced dark backgrounds, so answers rendered dark-on-dark
       (measured contrast 1.17:1 — invisible). The variables below pin the
       dark palette for the whole app, so contrast no longer depends on the
       visitor's system theme. Values mirror Gradio's own dark theme
       (neutral-100 on neutral-950); force_dark_js additionally switches
       Gradio's own dark styles on.
       ============================================ */
    .gradio-container {
        --body-background-fill: #0f0f0f;
        --body-text-color: #f4f4f5;
        --body-text-color-subdued: #a1a1aa;

        --background-fill-primary: #0f0f0f;
        --background-fill-secondary: #18181b;

        --block-background-fill: #1a1a1a;
        --block-border-color: #3f3f3f;
        --block-label-text-color: #a3a3a3;
        --block-title-text-color: #e5e5e5;
        --block-info-text-color: #a1a1aa;

        --panel-background-fill: #1a1a1a;
        --panel-border-color: #3f3f3f;

        --border-color-primary: #3f3f3f;
        --border-color-accent: #3b82f6;

        --input-background-fill: #1a1a1a;
        --input-background-fill-focus: #1a1a1a;
        --input-background-fill-hover: #1f1f1f;
        --input-border-color: #3f3f3f;
        --input-border-color-focus: #3b82f6;
        --input-border-color-hover: #52525b;
        --input-placeholder-color: #71717a;

        --code-background-fill: #161616;

        --table-border-color: #3f3f3f;
        --table-even-background-fill: #141414;
        --table-odd-background-fill: #1a1a1a;
        --table-text-color: #e5e5e5;

        --link-text-color: #60a5fa;
        --link-text-color-hover: #93c5fd;
        --link-text-color-active: #93c5fd;
        --link-text-color-visited: #a78bfa;

        --checkbox-background-color: #1a1a1a;
        --checkbox-border-color: #3f3f3f;
        --checkbox-label-background-fill: #1a1a1a;
    }

    /* ============================================
       MAIN CONTAINER
       ============================================ */
    .progress-text { 
        display: none !important;
    }
    
    .gradio-container { 
        max-width: 1000px !important;
        width: 100% !important;
        margin: 0 auto !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: #0f0f0f !important;
        color: var(--body-text-color) !important;
    }
    
    /* ============================================
       TABS
       ============================================ */
    button[role="tab"] {
        color: #a3a3a3 !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
    }
    
    button[role="tab"]:hover {
        color: #e5e5e5 !important;
    }
    
    button[role="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #ffffff !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    
    .tabs {
        border-bottom: none !important;
        border-radius: 0 !important;
    }
    
    .tab-nav {
        border-bottom: 1px solid #3f3f3f !important;
        border-radius: 0 !important;
    }
    
    button[role="tab"]::before,
    button[role="tab"]::after,
    .tabs::before,
    .tabs::after,
    .tab-nav::before,
    .tab-nav::after {
        display: none !important;
        content: none !important;
        border-radius: 0 !important;
    }
    
    #doc-management-tab {
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    
    /* ============================================
       BUTTONS
       ============================================ */
    button {
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    
    .primary {
        background: #3b82f6 !important;
        color: white !important;
    }
    
    .primary:hover {
        background: #2563eb !important;
        transform: translateY(-1px) !important;
    }
    
    .stop {
        background: #ef4444 !important;
        color: white !important;
    }
    
    .stop:hover {
        background: #dc2626 !important;
        transform: translateY(-1px) !important;
    }
    
    /* ============================================
       CHAT INPUT BOX
       ============================================ */
    textarea[placeholder="Type a message..."],
    textarea[data-testid*="textbox"]:not(#file-list-box textarea) {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: var(--body-text-color) !important;
    }
    
    textarea[placeholder="Type a message..."]:focus {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    textarea[placeholder="Type a message..."]::placeholder {
        color: var(--input-placeholder-color) !important;
    }
    
    .gr-text-input:has(textarea[placeholder="Type a message..."]),
    [class*="chatbot"] + * [data-testid="textbox"],
    form:has(textarea[placeholder="Type a message..."]) > div {
        background: transparent !important;
        border: none !important;
        gap: 12px !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) button,
    [class*="chatbot"] ~ * button[type="submit"] {
        background: transparent !important;
        border: none !important;
        padding: 8px !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) button:hover {
        background: rgba(59, 130, 246, 0.1) !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) {
        gap: 12px !important;
        display: flex !important;
    }
    
    /* ============================================
       FILE UPLOAD
       ============================================ */
    .file-preview, 
    [data-testid="file-upload"] {
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 5px !important;
        color: #ffffff !important;
        min-height: 200px !important;
    }
    
    .file-preview:hover, 
    [data-testid="file-upload"]:hover {
        border-color: #3b82f6 !important;
        background: #1f1f1f !important;
    }
    
    .file-preview *,
    [data-testid="file-upload"] * {
        color: #ffffff !important;
    }
    
    .file-preview .label,
    [data-testid="file-upload"] .label {
        display: none !important;
    }
    
    /* ============================================
       INPUTS & TEXTAREAS
       ============================================ */
    input, 
    textarea {
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 10px !important;
        color: #e5e5e5 !important;
        transition: border-color 0.2s ease !important;
    }
    
    input:focus, 
    textarea:focus {
        border-color: #3b82f6 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    textarea[readonly] {
        background: #1a1a1a !important;
        color: #e5e5e5 !important;
    }
    
    /* ============================================
       FILE LIST BOX
       ============================================ */
    #file-list-box {
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    
    #file-list-box textarea {
        background: transparent !important;
        border: none !important;
        color: #e5e5e5 !important;
        padding: 0 !important;
    }
    
    /* ============================================
       CHATBOT CONTAINER
       ============================================
       Gradio 6 puts the class `chatbot` on every markdown span of a message
       (`<span class="md chatbot prose">`), NOT on the chat panel. The previous
       `.chatbot { ... }` rule therefore painted each message's text block
       instead of the panel, which is why answer text sat on an unintended
       background. The panel is addressed through its elem_id (project/ui/
       gradio_app.py); markdown content stays transparent so it sits on the
       bubble it belongs to. */
    #chatbot-panel {
        border-radius: 5px !important;
        background: var(--block-background-fill) !important;
        border: none !important;
    }

    #chatbot-panel .prose {
        background: transparent !important;
    }

    #chatbot-panel .message-wrap,
    #chatbot-panel .bubble-wrap {
        gap: 8px !important;
        padding: 12px !important;
    }

    /* ============================================
       MESSAGE BUBBLES
       ============================================ */
    .message {
        border-radius: 10px !important;
    }

    .message.user {
        /* blue-600: white text clears WCAG AA (4.9:1) on it */
        background: #2563eb !important;
        color: white !important;
    }
    
    .message.bot {
        background: #1f1f1f !important;
        color: var(--body-text-color) !important;
        border: 1px solid #3f3f3f !important;
        width: fit-content !important;
        max-width: 90% !important;
    }

    /* Answer text, list items, citations and code inside a message follow the
       pinned body colour, so they stay readable whatever the theme mode the
       browser reports. Links keep their own accent colour. */
    #chatbot-panel .prose p,
    #chatbot-panel .prose li,
    #chatbot-panel .prose strong,
    #chatbot-panel .prose em,
    #chatbot-panel .prose blockquote,
    #chatbot-panel .prose th,
    #chatbot-panel .prose td,
    #chatbot-panel .prose h1,
    #chatbot-panel .prose h2,
    #chatbot-panel .prose h3,
    #chatbot-panel .prose h4 {
        color: var(--body-text-color) !important;
    }

    #chatbot-panel .message.user .prose p,
    #chatbot-panel .message.user .prose li,
    #chatbot-panel .message.user .prose strong,
    #chatbot-panel .message.user .prose em {
        color: #ffffff !important;
    }

    #chatbot-panel .prose pre,
    #chatbot-panel .prose code {
        background: var(--code-background-fill) !important;
        color: var(--body-text-color) !important;
        border: 1px solid #3f3f3f !important;
    }
    
    .message-row img {
        margin: 0px !important;
    }

    .avatar-container img {
        padding: 0px !important;
    }

    /* ============================================
       PROGRESS BAR
       ============================================ */
    .progress-bar-wrap {
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #1a1a1a !important;
    }

    .progress-bar {
        border-radius: 10px !important;
        background: #3b82f6 !important;
    }
    
    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #e5e5e5 !important;
    }

    p, label, span, li {
        color: inherit;
    }
    
    /* ============================================
       GLOBAL OVERRIDES
       ============================================ */
    * {
        box-shadow: none !important;
    }
    
    footer {
        visibility: hidden;
    }
"""

# Gradio derives its palette from the visitor's OS/browser theme. This script
# pins the app to dark mode so Gradio's own dark styles apply as well as the
# pinned CSS variables above (which stay in force even if this script is
# blocked, or if the theme is switched back to light from Settings).
force_dark_js = """
function reflectragForceDark() {
    document.documentElement.classList.add('dark');
    if (document.body) {
        document.body.classList.add('dark');
    }
}
reflectragForceDark();
document.addEventListener('DOMContentLoaded', reflectragForceDark);
setTimeout(reflectragForceDark, 800);
"""
