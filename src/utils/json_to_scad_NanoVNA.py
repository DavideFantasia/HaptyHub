import json, os, config

def generate_scad(json_filepath, scad_filepath):
    # 1. LOAD & PARSE DATA
    with open(json_filepath, 'r') as file:
        data = json.load(file)

    if isinstance(data, list):
            data = data[0]  

    board_title = data.get('board_title', 'FlowchartVNA')

    nodes = {}
    for n in data.get('children', []):
        cx = n['x'] + (n['width'] / 2.0)
        cy = n['y'] + (n['height'] / 2.0)
        nodes[n['id']] = {
            'x': cx, 'y': -cy, 
            'raw_x': cx, 'raw_y': cy
        }

    edges = []
    all_x = [n['x'] for n in nodes.values()]
    all_y = [n['y'] for n in nodes.values()]

    for e in data.get('edges', []):
        src, tgt = nodes[e['source']], nodes[e['target']]
        label = e.get('labels', [{'text': None}])[0]['text'] if e.get('labels') else None

        for section in e.get('sections', []):
            raw_pts = [section['startPoint']] + section.get('bendPoints', []) + [section['endPoint']]
            raw_pts[0], raw_pts[-1] = {'x': src['raw_x'], 'y': src['raw_y']}, {'x': tgt['raw_x'], 'y': tgt['raw_y']}
            scad_pts = [[p['x'], -p['y']] for p in raw_pts]
            edges.append({'points': scad_pts, 'label': label})
            
            all_x.extend([p[0] for p in scad_pts])
            all_y.extend([p[1] for p in scad_pts])

    if not all_x:
        print("No nodes found in JSON!")
        return

    main_spine_x = list(nodes.values())[0]['x'] # Use the Start node as the center anchor
    max_reach_x = max([abs(x - main_spine_x) for x in all_x])
    
    min_x = main_spine_x - max_reach_x
    max_x = main_spine_x + max_reach_x
    
    min_y, max_y = min(all_y), max(all_y)
    
    base_width = 150
    base_height = 210
    block_size = 12.6
    margin_x = 15
    margin_y = 15
    safe_margin_x = margin_x + (block_size / 2)
    safe_margin_y = margin_y + (block_size / 2)

    grid_spacing_x = (base_width - (safe_margin_x * 2)) / max(1, (max_x - min_x))
    grid_spacing_y = (base_height - (safe_margin_y * 2)) / max(1, (max_y - min_y))
    x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing_x)
    y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing_y)
    
    def get_px(scad_x):
        return scad_x * grid_spacing_x + x_offset

    # =========================================================================
    # --- CALCULATE THE Y-CUT FOR SPLITTING IN 2 PARTS ---
    node_extents = []
    for n in nodes.values():
        actual_y = n['y'] * grid_spacing_y + y_offset 
        node_extents.append((actual_y - 12, actual_y + 12))
    
    node_extents.sort()

    max_gap = 0
    cut_y = base_height / 2.0
    for i in range(len(node_extents) - 1):
        gap = node_extents[i+1][0] - node_extents[i][1]
        if gap > max_gap and gap > 5: 
            max_gap = gap
            cut_y = node_extents[i][1] + (gap / 2.0)

    peg_edge_offset = 15.0 
    left_peg_x = peg_edge_offset
    right_peg_x = base_width - peg_edge_offset
    # =========================================================================
    
    # 2. OPENSCAD TEMPLATE
    scad_header = f"""// --- GLOBAL SETTINGS ---
    
use <{os.path.join(config.UTILS_DIR, 'braille.scad')}>; // library for the braille text
$fn = 32;
base_width = {base_width};
base_height = {base_height};
base_thickness = 4;
relief_depth = 2; 
recess_radius = 1;

block_size = {block_size};
post_size = 3;
post_height = 3;
edge_radius = 1; 
shape_radius = (block_size / 2); 

gap = 1.0; 
arrow_length = 4;
arrow_width = 3.5;

// --- WIRE ROUTING ---
wire_groove_width = 2.5; 
wire_groove_depth = 1.5; 

// --- DYNAMIC GRID ---
min_x = {min_x}; max_x = {max_x};
min_y = {min_y}; max_y = {max_y};
// Calculate X and Y scaling independently
grid_spacing_x = {grid_spacing_x};
grid_spacing_y = {grid_spacing_y};
         
x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing_x);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing_y);


// Apply X scale to the X coordinate, and Y scale to the Y coordinate
function scale_p(p) = [p[0] * grid_spacing_x + x_offset, p[1] * grid_spacing_y + y_offset];

// --- MODULES ---
module node_relief(x, y) {{
    p = scale_p([x, y]);
    translate([p[0], p[1], base_thickness - relief_depth])
        cylinder(h = relief_depth + 0.1, d = block_size);
}}

module node_post(x, y) {{
    p = scale_p([x, y]);
    translate([p[0] - post_size/2, p[1] - post_size/2, base_thickness - relief_depth])
        cube([post_size, post_size, post_height]);
}}

// --- TRENCH FOR THE WIRE ---
module bottom_trench(x1, y1, x2, y2) {{
    start_x = min(x1, x2);
    start_y = min(y1, y2);
    w = abs(x2 - x1) + wire_groove_width;
    h = abs(y2 - y1) + wire_groove_width;
    translate([start_x - wire_groove_width/2, start_y - wire_groove_width/2, -0.1])
        cube([w, h, wire_groove_depth + 0.1]);
}}

// --- MODULES ---
module edge_segment(p1, p2, is_start=false, is_end=false) {{
    p1s = scale_p(p1); p2s = scale_p(p2);
    dx = p2s[0] - p1s[0]; dy = p2s[1] - p1s[1];
    dist = sqrt(dx*dx + dy*dy); angle = atan2(dy, dx);
    sg = is_start ? shape_radius + gap : 0;
    eg = is_end ? shape_radius + arrow_length + gap : 0;
    if (dist - sg - eg > 0) 
        translate([p1s[0] + cos(angle)*sg, p1s[1] + sin(angle)*sg, base_thickness]) 
            rotate([0, 90, angle]) 
                cylinder(h = dist - sg - eg + 0.1, r = edge_radius, $fn=24);
}}

module edge_elbow(p) {{ 
    v = scale_p(p); 
    translate([v[0], v[1], base_thickness]) sphere(r = edge_radius, $fn=32); 
}}

module edge_arrow(p1, p2) {{
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    translate([p2s[0] - cos(angle)*(shape_radius+gap), p2s[1] - sin(angle)*(shape_radius+gap), base_thickness]) 
        rotate([0, 0, angle]) 
            linear_extrude(height = edge_radius) 
                polygon(points=[[0, 0], [-arrow_length , -arrow_width/2], [-arrow_length, arrow_width/2]]);
}}

// --- RENDERING ---
module full_board() {{
    union() {{
        difference() {{
            cube([base_width, base_height, base_thickness]);
"""

    scad_lines = [scad_header]

    for n in nodes.values():
        scad_lines.append(f"            node_relief({n['x']}, {n['y']});")

    # =========================================================================
    # --- TRENCH ROUTING  ---
    scad_lines.append("\n            // --- Continuous Snake Routing (Entry & Exit Adjacent) ---")
    
    unique_x_coords = sorted(list(set(round(get_px(n['x']), 2) for n in nodes.values())))
    N = len(unique_x_coords)
    
    wire_margin = 8
    top_y = base_height - wire_margin
    bot_y = wire_margin
    ret_y = 3   
    exit_y = -1 
    
    # ENTRY POINT (Column 0 goes from bottom edge to top margin)
    scad_lines.append(f"            bottom_trench({unique_x_coords[0]}, {exit_y}, {unique_x_coords[0]}, {top_y}); // Entry")
    
    # ROUTING
    for i in range(N - 1):
        if i % 2 == 0:
            # At Top: Route Right, then Down
            scad_lines.append(f"            bottom_trench({unique_x_coords[i]}, {top_y}, {unique_x_coords[i+1]}, {top_y});")
            scad_lines.append(f"            bottom_trench({unique_x_coords[i+1]}, {top_y}, {unique_x_coords[i+1]}, {bot_y});")
        else:
            # At Bottom: Route Right, then Up
            scad_lines.append(f"            bottom_trench({unique_x_coords[i]}, {bot_y}, {unique_x_coords[i+1]}, {bot_y});")
            scad_lines.append(f"            bottom_trench({unique_x_coords[i+1]}, {bot_y}, {unique_x_coords[i+1]}, {top_y});")
            
    # END-OF-LINE & RETURN
    if N % 2 == 1:
        # Ended at TOP. Create a dummy drop column 9mm to the right of the last column.
        px_dummy = round(unique_x_coords[-1] + 9, 2)
        scad_lines.append(f"            bottom_trench({unique_x_coords[-1]}, {top_y}, {px_dummy}, {top_y}); // Top connector to dummy")
        scad_lines.append(f"            bottom_trench({px_dummy}, {top_y}, {px_dummy}, {ret_y}); // Dummy Drop Column")
        current_x = px_dummy
    else:
        # Ended at BOTTOM. Just extend the current column down a bit further to the return path level.
        scad_lines.append(f"            bottom_trench({unique_x_coords[-1]}, {bot_y}, {unique_x_coords[-1]}, {ret_y}); // Drop to return path")
        current_x = unique_x_coords[-1]
        
    # 4. HORIZONTAL RETURN & EXIT
    px_exit = round(unique_x_coords[0] + 9, 2) # Exit point is exactly 9mm to the right of Entry
    scad_lines.append(f"            bottom_trench({current_x}, {ret_y}, {px_exit}, {ret_y}); // Horizontal Return Path")
    scad_lines.append(f"            bottom_trench({px_exit}, {ret_y}, {px_exit}, {exit_y}); // Exit Point")
    # =========================================================================

    scad_lines.append("        } // End difference\n")

    for n in nodes.values():
        scad_lines.append(f"        node_post({n['x']}, {n['y']});")

    for e in edges:
        pts = e['points']
        for i in range(len(pts) - 1):
            is_start = "true" if i == 0 else "false"
            is_end = "true" if i == len(pts) - 2 else "false"
            scad_lines.append(f"        edge_segment({pts[i]}, {pts[i+1]}, {is_start}, {is_end});")
            if i > 0: 
                scad_lines.append(f"        edge_elbow({pts[i]});")
        scad_lines.append(f"        edge_arrow({pts[-2]}, {pts[-1]});")

    scad_lines.append("\n        // --- TACTILE TITLE ---")
    scad_lines.append("        translate([5, base_height - 10, base_thickness])")     
    scad_lines.append(f"            braille(\"{board_title}\");")

    scad_lines.append("    }") # Close union
    scad_lines.append("}")     # Close full_board module

    scad_lines.append("""
// --- SPLITTER LOGIC ---
module puzzle_tab_shape(inflate=0) {
    offset(delta=inflate) {
        polygon([
            [-4, -0.1], // Bottom Left 
            [ 4, -0.1], // Bottom Right
            [ 7,  6.0], // Top Right 
            [-7,  6.0]  // Top Left
        ]);
    }
}
""")

    core_scad = "\n".join(scad_lines)

    # -------------------------------------------------------------------------
    # Bottom Part
    part1_scad = core_scad + f"""
// RENDER PART 1 (BOTTOM)
intersection() {{
    full_board();
    translate([0, 0, -10]) linear_extrude(50) {{
        union() {{
            // Keep everything below the cut line
            translate([-500, -500]) square([1000, 500 + {cut_y}]);
            
            // Add two puzzle pegs anchored to the outer edges
            translate([{left_peg_x}, {cut_y}]) puzzle_tab_shape(0);
            translate([{right_peg_x}, {cut_y}]) puzzle_tab_shape(0);
        }}
    }}
}}
"""
    file1 = scad_filepath.replace('.scad', '_lower.scad')
    with open(file1, 'w') as f: f.write(part1_scad)
    print(f"Successfully generated: {file1}")

    # -------------------------------------------------------------------------
    # Top Part
    
    part2_scad = core_scad + f"""
// RENDER PART 2 (TOP)
intersection() {{
    full_board();
    translate([0, 0, -10]) linear_extrude(50) {{
        difference() {{
            // Keep everything above the cut line
            translate([-500, {cut_y}]) square([1000, 500]);
            
            // Subtract the holes anchored to the outer edges
            translate([{left_peg_x}, {cut_y}]) puzzle_tab_shape(0.2);
            translate([{right_peg_x}, {cut_y}]) puzzle_tab_shape(0.2);
        }}
    }}
}}
"""
    file2 = scad_filepath.replace('.scad', '_upper.scad')
    with open(file2, 'w') as f: f.write(part2_scad)
    print(f"Successfully generated: {file2}")

    # -------------------------------------------------------------------------
    # Full Board

    part3_scad = core_scad + """
// RENDER FULL PREASSEMBLED BOARD
full_board();
"""
    file3 = scad_filepath.replace('.scad', '.scad')
    with open(file3, 'w') as f: f.write(part3_scad)
    print(f"Successfully generated: {file3}")