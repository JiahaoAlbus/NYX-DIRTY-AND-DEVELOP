# Demo Script

## Purpose
A 10-minute guided demonstration of the NYX system, suitable for live presentations or video recording.

## Setup
1.  Start the backend:
    ```bash
    ./scripts/nyx_backend_dev.sh
    ```
2.  Launch the Web World (in a separate terminal):
    ```bash
    cd apps/nyx-world && npm run dev
    ```
3.  (Optional) Launch iOS Simulator.

## Scenario 1: The "Happy Path" (5 mins)

1.  **Open Web Portal**: Navigate to `http://localhost:5173`.
2.  **Show "Offline"**: Before backend is ready, show the "Backend Offline" banner. (Demonstrates "No Fake Data").
3.  **Connect**: Backend comes online. Banner disappears.
4.  **Create Identity**:
    -   Go to **Wallet**.
    -   Click "Load Wallet from Seed" (Seed: `123`).
    -   Show Balance (Testnet funds).
5.  **Execute Transaction**:
    -   Go to **Exchange**.
    -   Place a **BUY** order (Asset: `asset-a`, Amount: `10`, Price: `5`).
    -   Click "Place Order".
6.  **Verify Evidence**:
    -   Go to **Evidence** tab.
    -   Show the latest **Receipt**.
    -   Highlight `run_id`, `state_hash`, and `receipt_hash`.
    -   Explain: "This receipt proves the order was placed deterministically."

## Scenario 2: The "Offline/Failure" Path (2 mins)

1.  **Kill Backend**: Ctrl+C in the backend terminal.
2.  **Verify UI**: The Web Portal should immediately show "Backend Offline" or fail to load data.
3.  **Attempt Action**: Try to click "Refresh Balance".
4.  **Result**: Error message or disabled button.
5.  **Talking Point**: "We don't cache fake data. If the evidence chain is broken, the system stops."

## Scenario 3: Export & Verify (3 mins)

1.  **Restart Backend**.
2.  **Generate Evidence**: Run a quick smoke test script to generate volume.
    ```bash
    python scripts/nyx_smoke_all_modules.py --run-id demo-live
    ```
3.  **Export**:
    -   Go to **Evidence** tab.
    -   Click "Fetch Export Bundle".
    -   Download the ZIP.
4.  **Inspect**:
    -   Unzip the file.
    -   Show the JSON files (inputs, outputs, evidence).
    -   Talking Point: "This ZIP contains the cryptographic proof of everything we just did."
