# GameBuddy Focus Tracker: UI/UX Design for Overlay Widget

## 1. Design Philosophy

The UI/UX for the GameBuddy Focus Tracker widget is guided by the following principles:

*   **Minimalism & Non-Intrusiveness:** The widget must provide valuable information without distracting the gamer or obscuring critical game interface elements. It should be lightweight in appearance and feel.
*   **Clarity at a Glance:** Key metrics and the current buddy message should be easily understandable with a quick look.
*   **Intuitive Feedback:** Color coding and simple visual cues will be used to convey the user's state instantly.
*   **User Control & Customization:** Users should have control over the widget's position, appearance (e.g., transparency), and notification behavior.
*   **Coaching Persona:** The visual language and message presentation should reinforce the supportive, coaching nature of the AI buddy.

## 2. Widget Layout & Components

The widget will be a compact overlay, typically positioned in a screen corner (user-configurable).

### 2.1. Main Widget View (Default State)

*   **Arrangement:** A vertical or horizontal stack of elements, depending on user preference and available screen real estate.
    *   **Option A (Vertical Stack - Compact):**
        *   Buddy Message Area (Top, small text area)
        *   Attention Bar (%)
        *   Engagement Bar (%)
        *   Frustration Bar (%)
        *   Fatigue Bar (%)
        *   Distraction Bar (%)
    *   **Option B (Horizontal Layout - Wider):**
        *   [Buddy Message] [Att: XX%] [Eng: XX%] [Fru: XX%] [Fat: XX%] [Dis: XX%]
*   **Metric Display:**
    *   Each metric (Attention, Fatigue, Frustration, Engagement, Distraction) will be displayed as a thin progress bar.
    *   The percentage value (e.g., "87%") will be displayed next to or within the bar.
    *   **Color Coding for Bars:**
        *   **Attention:** Green (high) to Yellow (medium) to Red (low).
        *   **Engagement:** Green (high) to Yellow (medium) to Blue/Neutral (low).
        *   **Frustration:** Green (low) to Yellow (medium) to Red (high).
        *   **Fatigue:** Green (low) to Yellow (medium) to Red (high).
        *   **Distraction:** Green (low) to Yellow (medium) to Red (high).
*   **Buddy Message Area:**
    *   A small, dedicated text area to display the current coaching message or tip.
    *   Text will be concise.
    *   Messages will update dynamically but not too frequently to avoid distraction (as per state classification logic and cooldowns).

### 2.2. Expanded View / Settings Access (Optional)

*   A small, unobtrusive icon (e.g., a gear or the buddy's avatar) on the widget could allow access to an expanded view or a separate settings panel.
*   This view would allow for:
    *   Calibration initiation.
    *   Widget customization (position, transparency, scale).
    *   Notification preferences.
    *   Viewing unlocked rewards/achievements.
    *   Enabling/disabling features like adaptive coaching or the reward system.

## 3. Visual Design

*   **Style:** Modern, clean, and slightly 
