# Texas Hold'em CFR training

Train an abstracted multi-street CFR policy and benchmark it against the
heuristic and random agents:

```powershell
python train_and_eval.py --iterations 1000 --hands 1000
```

The script saves the policy to `models/cfr_policy.pkl` by default, reports the
number of discovered information sets and sampled preflop strategy changes,
then prints each agent's result in big blinds per 100 hands (bb/100). Use
`--model` to choose another policy path.