# Hardware Acquisition Decision Gate Model: From Cloud Scale to On-Prem CAPEX Justification

This document defines the mandatory, multi-stage **Decision Gate** process for evaluating the necessity of transitioning from a cloud-based OPEX model (renting compute power) to an on-premises CAPEX model (purchasing physical hardware). This gate is designed to prevent premature capital outlay based solely on current usage peaks or headline pricing models.

---

## I. Decision Gate Overview and Philosophy

**Goal:** To provide quantitative and qualitative justification that the annualized cost of ownership (TCO) for owned infrastructure will generate a significantly positive Return on Investment (ROI) compared to continued cloud consumption, while meeting defined operational resilience standards.

**Principle:** Hardware investment is treated as a strategic organizational commitment, not a tactical capacity upgrade. The decision must be *data-driven*, *holistic*, and *stress-tested* against failure scenarios.

---

## II. Pre-Gate Criteria: Data Collection (Minimum 90 Days)

Before any CAPEX modeling begins, the following evidence spanning at least ninety (90) consecutive days must be collected and averaged to establish baseline consumption and revenue patterns.

| Metric | Description | Required Evidence / Threshold Calculation | Purpose |
| :--- | :--- | :--- | :--- |
| **Utilization Rate ($\mu_{avg}$)** | Average CPU/GPU core utilization (%). Must exceed $X\%$. | 90-day average of peak vs. sustained usage. Identify idle capacity percentage and temporal load fluctuations. | Validates need for owned compute density. Low $\mu_{avg}$ negates CAPEX justification. |
| **Revenue Correlation ($\rho_R$)** | Correlation between measured cloud resource consumption ($C$) and direct revenue generation ($R$). | Calculate $R/C$ ratio over 90 days. Identify the minimum required sustained load to hit break-even cost coverage. | Determines if the business model can sustain the fixed costs of owned hardware. |
| **Model Mix ($\sigma_M$)** | Distribution of workloads by model type (e.g., LLM Inference, Fine-tuning, Training). | Percentage breakdown of compute hours consumed by different workload classes. Crucial for selecting appropriate accelerators (Tensor Core vs. standard GPU architecture). | Prevents purchasing generalist hardware when specialized high-density chips are needed. |
| **Concurrency ($N_{conc}$)** | Maximum sustained concurrent user sessions/APIs calls without degradation. | Peak measurements across 90 days, capturing peak spikes and recovery rates. | Determines required system throughput and network capacity (bandwidth bottleneck identification). |
| **Cost Elasticity ($\epsilon_C$)** | The sensitivity of total cloud cost to changes in model complexity or utilization rate. | $\Delta \text{Total Cost} / \Delta \text{Resource Load}$. Confirms if the marginal cost curve remains favorable for scaling up usage vs. owned capacity limits. | Validates that expected revenue growth exceeds OPEX increases. |

---

## III. The Full Total Cost of Ownership (TCO) Model

The CAPEX decision must compare the **Total Cost of Ownership (TCO)** over a defined timeframe ($T_{payback}$, e.g., 3 years) against the historical and projected OPEX (Cloud Renting).

$$\text{Decision} = \min (\text{OPEX}_{90+Days}, \text{CAPEX}_{\text{Initial}} + \sum_{t=1}^{T_{\text{payback}}} \text{Annualized Costs}_t)$$

### A. CAPEX Components (The Purchase)
1.  **Accelerators:** Total cost of $N$ GPUs (e.g., 4x H200). Requires *at least two comparable vendor quotes* detailing specific models and quantities ($C_{GPU}$).
2.  **Server Infrastructure:** Compute nodes, motherboards, memory capacity ($C_{SERVER}$).
3.  **Cooling & Power:** Dedicated HVAC units, PDU upgrades (kW), necessary rack space ($C_{POWER/COOL}$). *This cost is often underestimated.*
4.  **Networking:** Inter-GPU interconnects (e.g., NVLink fabric expansion), dedicated switches ($C_{NETWORK}$).
5.  **Contingency & Spares:** Buffer for failure/replacement GPUs, storage redundancy, networking components ($C_{SPARE}$).

### B. Annualized Operating Expenditure ($\text{Annual Costs}_t$)
1.  **Power Consumption Cost (OPEX):** $P_{\text{total}} \times H_{\text{op}} \times \text{Energy Rate} (\$/kWh)$. Must factor in expected power density and PUE (Power Usage Effectiveness).
2.  **Facility/Rack Hosting:** Annual depreciation, rent, maintenance, physical security ($C_{FACILITY}$).
3.  **Operational Overhead:** Dedicated engineering time for patching, cooling management, liquid cooling system upkeep ($C_{OPS}$ hours).
4.  **Financing/Depreciation (Hidden Cost):** Interest rates and depreciation schedule applied to the initial CAPEX outlay ($C_{FINANCE}$).
5.  **Downtime Cost ($\text{Cost}_{DOWN}$):** The modeled cost of downtime due to failure or maintenance, calculated as: $\text{Lost Revenue Rate} \times (\text{Mean Time To Repair} + \text{Failure Frequency})$. This must be costed into the TCO model and is non-negotiable.

---

## IV. Mandatory Constraints and Thresholds (The Gates)

### A. Technical & Operational Thresholds
1.  **Minimum Utilization Threshold ($\mu_{min}$):** The planned utilization rate of owned GPUs must exceed $75\%$ across a rolling 30-day average to justify the CAPEX outlay. Failure means continued cloud renting is superior.
2.  **Capacity Buffer ($N_{buffer}$):** The owned capacity must include provisions for at least **$2 \times N_{min}$** (where $N_{min}$ is the minimum required operational units) of spare, readily deployable capacity *after* factoring in cooling and rack limitations. This mitigates single-point failure risk.
3.  **Reliability/Failure Plan:** The design must mandate full **High Availability (HA)** architecture. No single machine or component can be a single point of failure. $N$ units require $\text{Redundancy Factor} \geq 1 + (2 / N)$.

### B. Financial Thresholds
1.  **Payback Period ($T_{payback}$):** The cumulative annual operational savings must drive the initial CAPEX investment back to zero within a predefined, acceptable period (e.g., $\leq 36$ months).
$$T_{\text{payback}} = \frac{\text{Total Initial CAPEX}}{\text{Average Annual Savings Generated}}$$
2.  **Break-Even Cost:** The fully loaded cost per compute hour ($\$/hr$) for owned hardware must be less than the projected long-term average cloud rate ($<\text{Cloud Rate}$).

### C. Legal & Regulatory Compliance Gate
1.  **Licensing Review:** Full audit of all necessary GPU vendor licenses, export control regulations (e.g., EAR in the US, relevant EU directives), and regional hosting restrictions for the intended deployment geography.
2.  **Data Residency Check:** Verification that physical hardware location satisfies all data sovereignty requirements related to model training and inference data storage.

---

## V. Execution Flow Summary: The Buy/Continue Renting Decision Matrix

| Stage | Action Required | Gate Criteria | Outcome & Next Step |
| :--- | :--- | :--- | :--- |
| **Stage 1: Data Collection** | Collect $\mu_{avg}$, $\rho_R$, and $\sigma_M$ for 90+ days. | Must meet baseline operational thresholds ($\text{Utilization} > X\%$). | If Failed: **STOP.** Continue OPEX (Cloud Rental). |
| **Stage 2: Sizing & TCO** | Run full TCO model comparing CAPEX vs. OPEX over $T_{payback}$. Calculate required redundancy ($N_{buffer}$). | Must achieve $\text{Payback} \leq T_{\text{max}}$ AND meet minimum utilization ($\mu_{min}$) at the proposed capacity level. | If Failed: **STOP.** Optimize existing usage/Process refinement (e.g., model compression). |
| **Stage 3: Vendor & Risk** | Obtain two or more comparable vendor quotes ($C_{GPU}, C_{SERVER}$). Finalize failure plan and calculate $\text{Cost}_{DOWN}$. | Must pass Legal Gate (Licensing/Export) AND demonstrate $\text{CAPEX} < \text{OPEX Savings}$ *even with included downtime cost*. | If Passed: **DECISION GATE APPROVED.** Initiate purchase procurement. |
| **Stage 4: Commitment** | Final executive sign-off on the full financial model and risk assessment report. | N/A | Implement owned hardware (CAPEX). Document remaining contingencies. |

***Note on Non-Compliance:** Failure to satisfy any criteria in Stages 1, 2, or 3 mandates continued cloud rental until the operational metrics improve.*