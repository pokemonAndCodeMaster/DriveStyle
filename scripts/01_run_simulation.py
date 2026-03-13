import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.core.vehicle import Vehicle
from src.core.controllers import FollowerController
from src.scenarios.car_following import LeadVehicleProfile, generate_scenario_configs

def run_simulation(config, duration=25.0, dt=0.02):
    lv_profile = LeadVehicleProfile(config["v_lv"], duration, dt)
    act = config["action"]
    if act == "constant": _, x_lv_list = lv_profile.constant_speed()
    elif act == "braking": _, x_lv_list = lv_profile.step_braking(start_time=5.0)
    elif act == "emergency": _, x_lv_list = lv_profile.emergency_braking(start_time=5.0)
    elif act == "accel": _, x_lv_list = lv_profile.slow_acceleration(start_time=5.0)
    elif act == "sine": _, x_lv_list = lv_profile.sine_wave()
        
    v_lv_list = lv_profile.v_profile
    ev = Vehicle(x0=x_lv_list[0] - config["d_init"], v0=config["v_ev"], dt=dt)
    controller = FollowerController(thw_k=config["style_k"], dt=dt)
    
    history = []
    timesteps = min(len(v_lv_list), int(duration / dt))
    
    for i in range(timesteps):
        state = ev.get_state()
        curr_x_ev, curr_v_ev, curr_a_ev = state["x"], state["v"], state["a"]
        curr_v_lv = v_lv_list[i]
        curr_x_lv = x_lv_list[i]
        dist = curr_x_lv - curr_x_ev
        
        a_cmd, a_base, a_corr = controller.compute_acceleration(curr_v_ev, curr_v_lv, dist)
        ev.update(a_cmd)
        
        history.append({
            "timestamp": i * dt, "v_lv": curr_v_lv, "v_ev": curr_v_ev, "a_ev": curr_a_ev,
            "dist": dist, "thw": dist / max(curr_v_ev, 0.5), "a_cmd": a_cmd,
            "a_base": a_base, "a_corr": a_corr, "gt_style": config["style_k"], "scenario": act
        })
        
    return pd.DataFrame(history)

def main():
    configs = generate_scenario_configs()
    all_data = []
    print(f"Starting simulation of {len(configs)} scenarios...")
    for idx, config in enumerate(configs):
        df = run_simulation(config)
        df["scenario_id"] = idx
        all_data.append(df)
        if (idx + 1) % 20 == 0:
            print(f"Finished {idx+1}/{len(configs)} scenarios")
            
    full_df = pd.concat(all_data)
    os.makedirs("output/data", exist_ok=True)
    out_path = "output/data/simulation_dataset.csv"
    full_df.to_csv(out_path, index=False)
    print(f"Simulation completed. Data saved to {out_path}")

if __name__ == "__main__":
    main()
