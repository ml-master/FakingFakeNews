# Faking Fake News for Real Fake News Detection: Propaganda-loaded Training Data Generation (ACL 2023)


[Kung-Hsiang (Steeve) Huang](https://khuangaf.github.io/), [Kathleen McKeown](https://www.cs.columbia.edu/~kathy), [Preslav Nakov](https://mbzuai.ac.ae/study/faculty/preslav-nakov), [Yejin Choi](https://homes.cs.washington.edu/~yejin/) and [Heng Ji](https://blender.cs.illinois.edu/hengji.html)


## How to use this repo

Please refer to the README within each model directory for specific instructions on how to run them.

## Data

The generated data and the test data used in my experiments are included in the `data` folder. `train.jsonl`, `dev.jsonl`, and `test.jsonl` are our generated data. `snopes_test.jsonl` and `politifact_test.jsonl` contain real and fake news from Snopes and PolitiFact.

The new data used are `gossipcop_train.jsonl`,`gossipcop_valid.jsonl`,and `gossipcop_test.jsonl`,which are extracted and processed from the FakeNewsNet dataset.




# Result 
The experimental results of the replication are presented in the table below.

| Dataset         | **ACC-T** | **ACC-F** | ACC   | AUC   | F1    |
|-----------------|-------|-------|-------|-------|-------|
| Original Result | -     | -     | 0.6534| -     | -     |
| SNOPES| 0.8584| 0.3134| 0.6056| 0.6075| 0.7543|
| politifact| 0.8224| 0.2834| 0.5835| 0.4851| 0.7369|
| politifact_Ablation| 0.2093| 0.7714| 0.4310| 0.5237| 0.3082|
| gossipcop| 0.7954| 0.2083| 0.5835| 0.4851| 0.7369|
| gossipcop_Ablation| 0.6673| 0.4065| 0.5587| 0.5646| 0.6382|

