import json
import csv
import os
import argparse
import numpy as np

def generate_mock_json(filename, target_thw=1.5, duration=20, dt=0.1):
    frames = []
    v_ego = 20.0  # 20 m/s
    dist = v_ego * target_thw
    for i in range(int(duration/dt)):
        t = i * dt
        # Adding slight noise
        curr_dist = dist + np.random.normal(0, 0.2)
        frame = {
            "timestamp": t,
            "23010101": [{"23010101_description_velocity": [v_ego], "23010101_description_acc_longi": [0.0]}],
            "17010900": [{
                "17010900_description_is_follow": [True],
                "17010900_description_front_id": [1],
                "17010900_description_following_distance": [curr_dist],
                "17010900_description_front_speed": [v_ego],
                "17010900_description_front_acc": [0.0]
            }]
        }
        frames.append(frame)
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(frames, f, indent=2)
    print(f"Generated JSON test case: {filename}")

def generate_mock_csv(filename, target_thw=1.5, duration=20, dt=0.1):
    v_ego = 20.0
    dist = v_ego * target_thw
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Headers standard for current CSV Loader
        writer.writerow(["timestamp", "ego_velocity", "ego_acceleration", "lead_velocity", "lead_acceleration", "relative_distance", "is_following", "target_id", "gt_style", "scenario"])
        for i in range(int(duration/dt)):
            t = i * dt
            curr_dist = dist + np.random.normal(0, 0.2)
            writer.writerow([t, v_ego, 0.0, v_ego, 0.0, curr_dist, 1, 1, target_thw, "constant_speed"])
    print(f"Generated CSV test case: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock car following test cases.")
    parser.add_argument("--out_json", default="tests/data/mock_case.json", help="Path to output JSON")
    parser.add_argument("--out_csv", default="tests/data/mock_case.csv", help="Path to output CSV")
    parser.add_argument("--thw", type=float, default=1.5, help="Target THW")
    args = parser.parse_args()
    
    generate_mock_json(args.out_json, target_thw=args.thw)
    generate_mock_csv(args.out_csv, target_thw=args.thw)
