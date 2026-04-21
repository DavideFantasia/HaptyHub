import itertools
import json
import math
import subprocess
import os
import copy



# ==========================================
# 2.PERMUTATIONS
# ==========================================

def get_port_object(node_id, side):
    """Generates the strict ELK port syntax you defined in your prompt."""
    return {
        "id": f"{node_id}_out_{side.lower()}",
        "layoutOptions": {"elk.port.side": side}
    }

def generate_topological_variations(base_layout):
    """
    Finds all nodes (Diamonds, Squares, Trapezoids), identifies their outgoing edges, 
    and creates a new JSON layout for every possible physical port combination.
    """
    edges = base_layout.get('edges', [])
    nodes = base_layout.get('children', [])

    # Group all outgoing edges by their source node
    out_edges_by_source = {}
    for e in edges:
        out_edges_by_source.setdefault(e['source'], []).append(e)

    options_per_node = []
    
    for node in nodes:
        n_id = node['id']
        
        # Count how many edges TARGET this node
        in_edges = [e for e in edges if e.get('target') == n_id]
        
        # If a node has ZERO incoming edges, it is the Start node! 
        # Skip it so it strictly keeps its SOUTH port.
        if len(in_edges) == 0:
            continue 
            
        out_edges = out_edges_by_source.get(n_id, [])
        
        # If it's a Decision Node (2 exits), test all 6 physical combinations
        if len(out_edges) == 2:
            combos = [('SOUTH', 'EAST'), ('SOUTH', 'WEST'), ('EAST', 'SOUTH'), 
                      ('WEST', 'SOUTH'), ('EAST', 'WEST'), ('WEST', 'EAST')]
            options_per_node.append([(n_id, out_edges[0]['id'], c[0], out_edges[1]['id'], c[1]) for c in combos])
            
        # If it's a standard Action/Input Node (1 exit), test South, East, and West
        elif len(out_edges) == 1:
            combos = ['SOUTH', 'EAST', 'WEST']
            options_per_node.append([(n_id, out_edges[0]['id'], c) for c in combos])

    if not options_per_node:
        return [base_layout]

    # Generate the list of all routing combinations
    all_combos = list(itertools.product(*options_per_node))
    variations = []

    for combo in all_combos:
        new_layout = copy.deepcopy(base_layout)
        
        for assignment in combo:
            n_id = assignment[0]
            node = next(n for n in new_layout['children'] if n['id'] == n_id)
            
            # Clear the outgoing ports for this node
            if 'ports' not in node: node['ports'] = []
            node['ports'] = [p for p in node['ports'] if not p['id'].startswith(f"{n_id}_out_")]
            
            # Apply 2-edge permutations (Diamonds)
            if len(assignment) == 5:
                _, e1_id, p1_side, e2_id, p2_side = assignment
                
                e1 = next(e for e in new_layout['edges'] if e['id'] == e1_id)
                e1['sourcePort'] = f"{n_id}_out_{p1_side.lower()}"
                node['ports'].append(get_port_object(n_id, p1_side))

                e2 = next(e for e in new_layout['edges'] if e['id'] == e2_id)
                e2['sourcePort'] = f"{n_id}_out_{p2_side.lower()}"
                node['ports'].append(get_port_object(n_id, p2_side))
                
            # Apply 1-edge permutations (Trapezoids/Squares)
            elif len(assignment) == 3:
                _, e1_id, p1_side = assignment
                
                e1 = next(e for e in new_layout['edges'] if e['id'] == e1_id)
                e1['sourcePort'] = f"{n_id}_out_{p1_side.lower()}"
                node['ports'].append(get_port_object(n_id, p1_side))

        variations.append(new_layout)

    return variations
# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_line_segments(edge):
    segments = []
    for section in edge.get('sections', []):
        pts = [section['startPoint']] + section.get('bendPoints', []) + [section['endPoint']]
        for i in range(len(pts) - 1):
            segments.append((pts[i], pts[i+1]))
    return segments

def do_lines_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C['y'] - A['y']) * (B['x'] - A['x']) > (B['y'] - A['y']) * (C['x'] - A['x'])
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def count_edge_node_overlaps(data):
    nodes = data.get('children', [])
    edges = data.get('edges', [])
    overlaps = 0
    for edge in edges:
        for seg_start, seg_end in get_line_segments(edge):
            for node in nodes:
                nx, ny, nw, nh = node.get('x', 0), node.get('y', 0), node.get('width', 0), node.get('height', 0)
                box_lines = [
                    ({'x': nx, 'y': ny}, {'x': nx+nw, 'y': ny}),
                    ({'x': nx+nw, 'y': ny}, {'x': nx+nw, 'y': ny+nh}),
                    ({'x': nx+nw, 'y': ny+nh}, {'x': nx, 'y': ny+nh}),
                    ({'x': nx, 'y': ny+nh}, {'x': nx, 'y': ny})
                ]
                for box_start, box_end in box_lines:
                    if do_lines_intersect(seg_start, seg_end, box_start, box_end):
                        overlaps += 1
    return overlaps

def count_edge_crossings(data):
    all_segments = []
    for edge in data.get('edges', []):
        all_segments.extend(get_line_segments(edge))
    crossings = 0
    for i in range(len(all_segments)):
        for j in range(i + 1, len(all_segments)):
            p1, p2 = all_segments[i]
            p3, p4 = all_segments[j]
            if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4: continue
            if do_lines_intersect(p1, p2, p3, p4): crossings += 1
    return crossings


def get_total_edge_length(data):
    length = 0
    for edge in data.get('edges', []):
        for p1, p2 in get_line_segments(edge):
            length += math.sqrt((p2['x'] - p1['x'])**2 + (p2['y'] - p1['y'])**2)
    return length

def get_port_flow_penalty(data):
    """
    Calculates how far the layout deviates from perfect North-to-South flow.
    Rewards edges that exit SOUTH and enter NORTH.
    """
    penalty_score = 0
    for edge in data.get('edges', []):
        src_port = edge.get('sourcePort', '').lower()
        tgt_port = edge.get('targetPort', '').lower()

        # 1. Evaluate Outgoing (Source) Ports
        if 'east' in src_port or 'west' in src_port:
            penalty_score += 1   # Standard penalty for horizontal branching
        elif 'north' in src_port:
            penalty_score += 10  # Massive penalty for exiting backwards out the top!

        # 2. Evaluate Incoming (Target) Ports
        if 'east' in tgt_port or 'west' in tgt_port:
            penalty_score += 1   # Standard penalty for arriving from the side
        elif 'south' in tgt_port:
            penalty_score += 10  # Massive penalty for entering from the bottom!
            
    return penalty_score


# ==========================================
# 4. LOOP
# ==========================================

def clean_floats(data):
    """Recursively rounds all spatial values to integers."""
    if isinstance(data, dict):
        for k, v in data.items():
            # If the key is a coordinate or dimension, round it
            if k in ['x', 'y', 'width', 'height'] and isinstance(v, (int, float)):
                data[k] = int(round(v))
            else:
                clean_floats(v)
    elif isinstance(data, list):
        for item in data:
            clean_floats(item)


def run_elk_batch(batch_list):
    """Sends the ENTIRE list of configurations to Node.js at once."""
    batch_in = 'batch_in.json'
    batch_out = 'batch_out.json'
    
    with open(batch_in, 'w') as f:
        json.dump(batch_list, f)
        
    try:
        # This calls Node ONCE.
        subprocess.run(["node", "run_elk_gs.js", batch_in, batch_out], check=True, capture_output=True)
        
        with open(batch_out, 'r') as f:
            return json.load(f)
            
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else "Unknown JS Error"
        print(f"JS BATCH CRASH: {error_msg}")
        return [] 
    finally:
        # Clean up temp files
        if os.path.exists(batch_in): os.remove(batch_in)
        if os.path.exists(batch_out): os.remove(batch_out)

def perform_grid_search(base_json_file):
    with open(base_json_file, 'r') as f:
        base_layout = json.load(f)

    # 1. Generate all the variations in Python
    print("Generating topological port permutations...")
    topological_variations = generate_topological_variations(base_layout)
    total_runs = len(topological_variations)
    
    print(f"Starting Batch Search... Sending {total_runs} combinations to ELK.")
    
    solved_batch = run_elk_batch(topological_variations)
    
    if not solved_batch:
        print("Batch processing failed. No layouts returned.")
        return

    best_score = float('inf')
    best_layout = None
    
    for i, solved_layout in enumerate(solved_batch):
       
        # Grade it
        overlaps = count_edge_node_overlaps(solved_layout)
        crossings = count_edge_crossings(solved_layout)
        edge_len = get_total_edge_length(solved_layout)
        
        # --- THE NEW PORT FLOW CHECK ---
        port_flow = get_port_flow_penalty(solved_layout)
        
        # --- THE SCORING HIERARCHY ---
        # 2000/1000: No overlaps or crossings.
        # 250: Heavily punish non-SOUTH exits and non-NORTH entrances.
        # 0.1: Shorter total pipes win tie-breakers.
        
        score = (overlaps * 20000) + (crossings * 10000) + (port_flow * 200)  + (edge_len * 0.1)

        if score < best_score:
            best_score = score
            best_layout = solved_layout

    if best_layout:
        print("\n" + "="*40)
        print(f"Final Score: {best_score:.1f}")
        

        clean_floats(best_layout)
        with open('output_coordinates.json', 'w') as f:
            json.dump(best_layout, f, indent=2)
        print("Saved perfect blueprint to 'output_coordinates.json'.")
    else:
        print("\nERROR: No valid layouts were generated.")





if __name__ == "__main__":
    perform_grid_search('input_coordinates.json')