#!/usr/bin/env python3
"""
Plot Deployment Times
- Reads deployment_times.json
- Generates a bar chart showing deployment times per region
- Highlights failed deployments (ElapsedSeconds = 0) in red
"""

import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

TIMES_FILE = "deployment_times.json"

# --- Load JSON data ---
if not os.path.exists(TIMES_FILE):
    print(f"⚠️ {TIMES_FILE} not found!")
    exit(1)

with open(TIMES_FILE, "r") as f:
    data = json.load(f)

# --- Prepare data ---
regions = [entry["Region"] for entry in data]
times = [entry["ElapsedSeconds"] for entry in data]
colors = ["red" if t == 0 else "green" for t in times]  # failed deployments in red

# --- Plot ---
sns.set(style="whitegrid")
plt.figure(figsize=(10, 6))
bars = plt.bar(regions, times, color=colors)

# Add labels on top of bars
for bar, t in zip(bars, times):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f"{t:.2f}s", ha='center', va='bottom')

plt.title("AWS Deployment Times per Region")
plt.xlabel("Region")
plt.ylabel("Elapsed Time (seconds)")
plt.ylim(0, max(times) * 1.3)  # add some headroom for labels
plt.tight_layout()

# Save figure
plt.savefig("deployment_times.png", dpi=300)
print("📈 Deployment time graph saved as deployment_times.png")
plt.show()
