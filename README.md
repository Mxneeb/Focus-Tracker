# Focus Tracker - README

## Overview

Focus Tracker is a lightweight overlay widget that uses computer vision to track your face and emotional state during work, study, or any focused activity. It shows live stats like attention, fatigue, frustration, and engagement levels as percentages, and offers personalized, encouraging or helpful messages based on your mood.

This project aims to provide a supportive AI coach to help users manage their focus, improve productivity, and recognize when to take breaks during any task requiring sustained attention.

## Project Structure

-   `main.py`: Main entry point for the application.
-   `requirements.txt`: Python dependencies.
-   `core/`: Core logic modules (CV, metrics, state, feedback, etc.).
-   `ui/`: User interface components (widget, settings panel).
-   `data/`: Local data storage and management.
-   `config/`: Application configuration.
-   `assets/`: Image or sound assets for the UI.
-   `docs/`: Project documentation (specifications, design docs).
-   `tests/`: Unit and integration tests.

## Setup and Installation

1.  Clone the repository (if applicable).
2.  Create a Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```bash
    python main.py
    ```

## Key Documents

Refer to the `docs/` directory for detailed specifications:

-   `feature_and_behavior_specification.md`
-   `system_architecture.md`
-   `metric_algorithms.md`
-   `ui_ux_design.md`
-   `research_summary_cv.md`

## Contributing

(Details to be added if this becomes an open project)

## License

(License to be determined - likely MIT if open source)

