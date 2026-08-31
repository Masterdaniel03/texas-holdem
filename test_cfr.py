import time
from engine.cfr_trainer import CFRTrainer

def run_training():
    print("Initializing the CFR Time Machine...")
    trainer = CFRTrainer()
    
    start_time = time.time()
    
    trainer.train()
    
    end_time = time.time()
    
    print("\n=== TRAINING RESULTS ===")
    print(f"Time elapsed: {end_time - start_time:.2f} seconds")
    print(f"Total InfoSets discovered (Memory Size): {len(trainer.node_map)}")
    
    if trainer.node_map:
        sample_key = list(trainer.node_map.keys())[0]
        sample_node = trainer.node_map[sample_key]
        
        print(f"\nPeek into Memory - InfoSet: {sample_key}")
        print(f"Regret Sums (F, C, R): {sample_node.regret_sum}")
        
        avg_strat = [round(p * 100, 1) for p in sample_node.get_average_strategy()] 
        print(f"Master Strategy: Fold {avg_strat[0]}% | Call {avg_strat[1]}% | Raise {avg_strat[2]}%")

if __name__ == "__main__":
    run_training()