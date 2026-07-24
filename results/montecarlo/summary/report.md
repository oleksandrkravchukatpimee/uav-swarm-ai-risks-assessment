# Monte Carlo AHP Report

## Profile Acceptance

| Profile | Generated | Accepted | Accepted % |
|---|---:|---:|---:|
| P1 (AI/ML-heavy) | 200 | 191 | 95.50 |
| P2 (Swarm/Ops-heavy) | 200 | 183 | 91.50 |
| P3 (Balanced) | 200 | 190 | 95.00 |
| P4 (Safety/Validation-heavy) | 200 | 195 | 97.50 |

## Top Risks by Mean Weight

### P1 - AI/ML-heavy
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.3236, std=0.0336, median=0.3237
- Model Training / Technological / Confidence miscalibration: mean=0.1560, std=0.0220, median=0.1560
- Model Training / Technological / Confabulations: mean=0.1545, std=0.0204, median=0.1536
- Model operation / Technological / Cascading error propagation: mean=0.0922, std=0.0140, median=0.0905
- Knowledge analysis / Technological / Reliance on spurious features: mean=0.0415, std=0.0061, median=0.0412
- Model Training / Technological / Overfitting: mean=0.0366, std=0.0061, median=0.0362
- Model Training / Human / Domain shift: mean=0.0239, std=0.0052, median=0.0233
- Model Training / Human / Incomplete validation criteria: mean=0.0239, std=0.0049, median=0.0235
- Knowledge analysis / Human / Inappropriate model architecture: mean=0.0219, std=0.0037, median=0.0219
- Knowledge analysis / Human / Lack of uncertainty estimation: mean=0.0219, std=0.0037, median=0.0216

### P2 - Swarm/Ops-heavy
- Model operation / Technological / Cascading error propagation: mean=0.4385, std=0.0257, median=0.4412
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.0884, std=0.0163, median=0.0880
- Model operation / Human / Loss of situational awareness: mean=0.0708, std=0.0092, median=0.0691
- Model Training / Technological / Confabulations: mean=0.0576, std=0.0110, median=0.0585
- Model Training / Technological / Overfitting: mean=0.0576, std=0.0105, median=0.0572
- Model Training / Technological / Confidence miscalibration: mean=0.0572, std=0.0108, median=0.0579
- Model operation / Technological / Sensor artifacts: mean=0.0565, std=0.0077, median=0.0553
- Model operation / Technological / Concept drift: mean=0.0561, std=0.0077, median=0.0554
- Knowledge selection / Human / Data representativeness: mean=0.0267, std=0.0048, median=0.0265
- Knowledge selection / Human / Dataset bias: mean=0.0265, std=0.0047, median=0.0257

### P3 - Balanced
- Model operation / Technological / Cascading error propagation: mean=0.4173, std=0.0257, median=0.4176
- Model operation / Human / Loss of situational awareness: mean=0.0665, std=0.0084, median=0.0644
- Model operation / Technological / Sensor artifacts: mean=0.0528, std=0.0063, median=0.0527
- Model operation / Technological / Concept drift: mean=0.0526, std=0.0059, median=0.0523
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.0452, std=0.0103, median=0.0439
- Model Training / Human / Domain shift: mean=0.0449, std=0.0101, median=0.0445
- Model Training / Human / Incomplete validation criteria: mean=0.0446, std=0.0101, median=0.0443
- Knowledge analysis / Technological / Reliance on spurious features: mean=0.0438, std=0.0094, median=0.0434
- Knowledge analysis / Human / Lack of uncertainty estimation: mean=0.0299, std=0.0067, median=0.0291
- Knowledge analysis / Human / Annotation errors: mean=0.0293, std=0.0064, median=0.0289

### P4 - Safety/Validation-heavy
- Knowledge analysis / Technological / Incorrect spatial-geometric interpretation: mean=0.2537, std=0.0222, median=0.2508
- Model Training / Technological / Confidence miscalibration: mean=0.1663, std=0.0190, median=0.1674
- Model operation / Human / Loss of situational awareness: mean=0.1579, std=0.0246, median=0.1600
- Model operation / Technological / Cascading error propagation: mean=0.1278, std=0.0222, median=0.1278
- Model Training / Technological / Confabulations: mean=0.0777, std=0.0138, median=0.0770
- Knowledge analysis / Technological / Reliance on spurious features: mean=0.0332, std=0.0049, median=0.0323
- Model Training / Human / Incomplete validation criteria: mean=0.0320, std=0.0049, median=0.0316
- Knowledge analysis / Human / Lack of uncertainty estimation: mean=0.0298, std=0.0042, median=0.0289
- Model Training / Technological / Catastrophic forgetting: mean=0.0182, std=0.0031, median=0.0179
- Model Training / Technological / Overfitting: mean=0.0182, std=0.0027, median=0.0179

## Cross-profile

- Invariant risks (top-5 intersection): Knowledge analysis / Technological / Incorrect spatial-geometric interpretation, Model operation / Technological / Cascading error propagation
- Profile-sensitive risks (rank range >= 5): Knowledge analysis / Human / Annotation errors, Knowledge analysis / Human / Inappropriate model architecture, Knowledge analysis / Human / Lack of uncertainty estimation, Knowledge analysis / Technological / Reliance on spurious features, Knowledge selection / Human / Data representativeness, Knowledge selection / Human / Dataset bias, Model Training / Human / Domain shift, Model Training / Human / Incomplete validation criteria, Model Training / Technological / Catastrophic forgetting, Model Training / Technological / Confabulations, Model Training / Technological / Confidence miscalibration, Model Training / Technological / Overfitting, Model operation / Human / Loss of situational awareness, Model operation / Technological / Concept drift, Model operation / Technological / Sensor artifacts

### Ranking Correlations
- P1__P2: Spearman=0.6436, Kendall=0.4421
- P1__P3: Spearman=0.2962, Kendall=0.2211
- P1__P4: Spearman=0.7173, Kendall=0.5895
- P2__P3: Spearman=0.5233, Kendall=0.4421
- P2__P4: Spearman=0.7534, Kendall=0.5789
- P3__P4: Spearman=0.4391, Kendall=0.2947
