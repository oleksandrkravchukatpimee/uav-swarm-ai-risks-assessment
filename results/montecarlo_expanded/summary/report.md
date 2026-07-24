# Monte Carlo AHP Report

## Profile Acceptance

| Profile | Generated | Accepted | Accepted % |
|---|---:|---:|---:|
| P1 (AI/ML-heavy) | 200 | 198 | 99.00 |
| P2 (Swarm/Ops-heavy) | 200 | 188 | 94.00 |
| P3 (Balanced) | 200 | 197 | 98.50 |
| P4 (Safety/Validation-heavy) | 200 | 199 | 99.50 |

## Top Risks by Mean Weight

### P1 - AI/ML-heavy
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.1460, std=0.0165, median=0.1472
- Knowledge analysis / Technological / Pseudo-quantification risk: mean=0.1451, std=0.0165, median=0.1441
- Model training / Technological / Confidence miscalibration: mean=0.0684, std=0.0088, median=0.0679
- Model training / Technological / Confabulations: mean=0.0677, std=0.0097, median=0.0675
- Model training / Technological / Noise/blur/compression fragility: mean=0.0250, std=0.0036, median=0.0246
- Model training / Technological / Metric gaming: mean=0.0249, std=0.0035, median=0.0249
- Model training / Technological / Domain shift as technological robustness failure: mean=0.0249, std=0.0033, median=0.0251
- Model training / Technological / Preprocessing and augmentation pipeline defects: mean=0.0249, std=0.0034, median=0.0248
- Model training / Technological / Training instability: mean=0.0249, std=0.0035, median=0.0245
- Model training / Technological / Correlated error structure omission: mean=0.0248, std=0.0033, median=0.0246

### P2 - Swarm/Ops-heavy
- Model operation / Technological / Dynamic topology: mean=0.0941, std=0.0075, median=0.0939
- Model operation / Technological / Cascading error propagation: mean=0.0937, std=0.0071, median=0.0939
- Model operation / Technological / Correlated perception errors: mean=0.0935, std=0.0073, median=0.0935
- Model operation / Technological / Collective robustness loss: mean=0.0934, std=0.0072, median=0.0936
- Model operation / Technological / Communication loss / swarm fragmentation: mean=0.0931, std=0.0064, median=0.0930
- Knowledge analysis / Technological / Correlated errors x interaction graph omission: mean=0.0540, std=0.0102, median=0.0534
- Model operation / Human / Loss of situational awareness: mean=0.0466, std=0.0058, median=0.0455
- Model training / Technological / Correlated error structure omission: mean=0.0462, std=0.0081, median=0.0462
- Model training / Technological / Noise/blur/compression fragility: mean=0.0229, std=0.0043, median=0.0229
- Model training / Technological / Overfitting: mean=0.0228, std=0.0040, median=0.0228

### P3 - Balanced
- Model operation / Technological / Cascading error propagation: mean=0.1656, std=0.0128, median=0.1659
- Model operation / Technological / Map inconsistency: mean=0.0611, std=0.0064, median=0.0611
- Model operation / Technological / Security robustness / spoofing: mean=0.0607, std=0.0063, median=0.0602
- Model operation / Technological / Concept drift: mean=0.0601, std=0.0054, median=0.0600
- Model operation / Technological / Sensor artifacts: mean=0.0600, std=0.0060, median=0.0598
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.0485, std=0.0083, median=0.0479
- Model operation / Human / Loss of situational awareness: mean=0.0441, std=0.0057, median=0.0433
- Model training / Human / Overestimation due to data leakage / wrong splits: mean=0.0358, std=0.0072, median=0.0347
- Model training / Human / Domain shift underestimation: mean=0.0354, std=0.0067, median=0.0343
- Knowledge analysis / Human / Inappropriate model architecture: mean=0.0225, std=0.0048, median=0.0224

### P4 - Safety/Validation-heavy
- Knowledge analysis / Technological / Reliance on spurious features: mean=0.1748, std=0.0161, median=0.1728
- Model operation / Human / Policy misconfiguration: mean=0.0678, std=0.0117, median=0.0667
- Model operation / Human / Loss of situational awareness: mean=0.0669, std=0.0111, median=0.0665
- Model training / Technological / Confidence miscalibration: mean=0.0603, std=0.0071, median=0.0608
- Model training / Technological / Selective prediction / refusal failure: mean=0.0601, std=0.0069, median=0.0603
- Model operation / Technological / Fallback failure / controlled degradation failure: mean=0.0394, std=0.0061, median=0.0396
- Model operation / Technological / Collective robustness loss: mean=0.0394, std=0.0061, median=0.0394
- Model training / Technological / Overfitting: mean=0.0291, std=0.0038, median=0.0292
- Model training / Technological / Domain shift as technological robustness failure: mean=0.0288, std=0.0043, median=0.0290
- Model training / Technological / Noise/blur/compression fragility: mean=0.0288, std=0.0038, median=0.0288

## Cross-profile

- Invariant risks (top-5 intersection): None
- Profile-sensitive risks (rank range >= 5): Knowledge analysis / Human / Annotation errors, Knowledge analysis / Human / Assumption mismatch about sensors and communication, Knowledge analysis / Human / HSI / operator-loop omission, Knowledge analysis / Human / Inappropriate model architecture, Knowledge analysis / Human / Incomplete or inadequate validation criteria, Knowledge analysis / Human / Lack of uncertainty estimation, Knowledge analysis / Human / Misdiagnosis of error causes, Knowledge analysis / Human / OOD / working-domain definition error, Knowledge analysis / Human / Swarm-in-the-loop omission, Knowledge analysis / Human / Task formulation mismatch, Knowledge analysis / Technological / Correlated errors x interaction graph omission, Knowledge analysis / Technological / Incorrect spatial-geometric interpretation, Knowledge analysis / Technological / Pseudo-quantification risk, Knowledge analysis / Technological / Reliance on spurious features, Knowledge analysis / Technological / Representation mismatch for swarm needs, Knowledge analysis / Technological / Spatial frame / map mismatch, Knowledge selection / Human / Data contamination / train-test leakage, Knowledge selection / Human / Data representativeness / representativeness gap, Knowledge selection / Human / Data-to-ops mismatch, Knowledge selection / Human / Dataset bias / spatial bias, Knowledge selection / Human / Label/metadata leakage, Knowledge selection / Human / Limited scene diversity, Knowledge selection / Human / Missing operational scenarios, Knowledge selection / Human / Operator/supervision mismatch, Knowledge selection / Human / Scale mismatch, Knowledge selection / Human / Temporal bias / seasonality, Knowledge selection / Technological / C2-mode mismatch, Knowledge selection / Technological / Class/event imbalance, Knowledge selection / Technological / Compression artifacts and data transformations, Knowledge selection / Technological / Correlated inter-agent errors not represented in data, Knowledge selection / Technological / Data format / pipeline mismatch, Knowledge selection / Technological / Georeferencing and sensor calibration errors, Knowledge selection / Technological / Latency/refresh-rate mismatch, Knowledge selection / Technological / OOD / unknown unknowns, Knowledge selection / Technological / Sensor heterogeneity, Knowledge selection / Technological / Weather/smoke/snow degradation coverage gap, Model operation / Human / Incorrect operator override, Model operation / Human / Loss of situational awareness, Model operation / Human / Mission drift, Model operation / Human / OPS gaps, Model operation / Human / Policy misconfiguration, Model operation / Technological / Cascading error propagation, Model operation / Technological / Collective robustness loss, Model operation / Technological / Communication loss / swarm fragmentation, Model operation / Technological / Concept drift, Model operation / Technological / Correlated perception errors, Model operation / Technological / Dynamic topology, Model operation / Technological / Fallback failure / controlled degradation failure, Model operation / Technological / Map inconsistency, Model operation / Technological / Model version skew, Model operation / Technological / On-board compute overload, Model operation / Technological / Security robustness / spoofing, Model operation / Technological / Sensor artifacts, Model training / Human / Domain shift underestimation, Model training / Human / Incomplete validation criteria, Model training / Human / Insufficient overfitting / regularization control, Model training / Human / Overestimation due to data leakage / wrong splits, Model training / Human / Reproducibility failure, Model training / Human / Wrong continual/online learning approach, Model training / Technological / Catastrophic forgetting, Model training / Technological / Confabulations, Model training / Technological / Confidence miscalibration, Model training / Technological / Correlated error structure omission, Model training / Technological / Domain shift as technological robustness failure, Model training / Technological / Latency/compute budget breach, Model training / Technological / Metric gaming, Model training / Technological / Noise/blur/compression fragility, Model training / Technological / Overfitting, Model training / Technological / Preprocessing and augmentation pipeline defects, Model training / Technological / Selective prediction / refusal failure, Model training / Technological / Training instability

### Ranking Correlations
- P1__P2: Spearman=0.6469, Kendall=0.4004
- P1__P3: Spearman=0.5396, Kendall=0.3883
- P1__P4: Spearman=0.6753, Kendall=0.5002
- P2__P3: Spearman=0.6904, Kendall=0.4680
- P2__P4: Spearman=0.5949, Kendall=0.4028
- P3__P4: Spearman=0.5880, Kendall=0.4165
