import json


def generate_scad(json_filepath, base_scad_filepath):
    # LOAD & PARSE DATA
    with open(json_filepath, 'r') as file:
        data = json.load(file)

        if isinstance(data, list):
            data = data[0]  


    # Store the dimensions of the tablet screen
    screen_width = data.get('screen_width', 0)
    screen_height = data.get('screen_height', 0)

    #================= EXPERIMENTAL ======================================

    # Margins for the bezels around the screen
    margin_top = data.get('margin_top', 18)       # Distance from top of screen to top edge of tablet
    margin_bottom = data.get('margin_bottom', 18) # Distance from bottom of screen to bottom edge
    margin_left = data.get('margin_left', 14)     # Distance from left of screen to left edge
    margin_right = data.get('margin_right', 14)   # Distance from right of screen to right edge
    

    tablet_actual_width = data.get('tablet_case_width', 164.2); # change back to 164.2 for Samsung Tablet
    tablet_actual_height = data.get('tablet_case_height', 254.2); # change back to 254.2 for Samsung Tablet


    # ===== CODE FOR THE PEGS TO CONNECT THE TWO HALVES OF THE PRINT =====
    # Distance from the physical edge of the plastic to the center of the peg
    peg_edge_offset = 15.0 
    
    left_peg_x = -margin_left + peg_edge_offset
    right_peg_x = -margin_left + tablet_actual_width - peg_edge_offset    

    #=====================================================================

    block_size = 17
    menu_radius = 8

    menu_x = screen_width - menu_radius - 5
    menu_y = screen_height - menu_radius - 5


    #=====================================================================

    # Title of the board
    board_title = data.get('board_title', 'Flowchart')  # Defaults to 'Flowchart' if not found


    #=====================================================================


    # Store nodes in a dictionary keyed by ID 
    nodes = {}
    for n in data.get('children', []):
        cx = n['x'] + (n['width'] / 2.0)
        cy = n['y'] + (n['height'] / 2.0)
        nodes[n['id']] = {
            'shape': n.get('myCustomShape', 'square'),
            'x': cx, 'y': -cy, 
            'raw_x': cx, 'raw_y': cy
        }

    edges = []
    # Track all coordinates to calculate the bounding box
    all_x = [n['x'] for n in nodes.values()]
    all_y = [n['y'] for n in nodes.values()]

    for e in data.get('edges', []):
        src, tgt = nodes[e['source']], nodes[e['target']]
        label = e.get('labels', [{'text': None}])[0]['text'] if e.get('labels') else None

        for section in e.get('sections', []):
            raw_pts = [section['startPoint']] + section.get('bendPoints', []) + [section['endPoint']]

            raw_pts[0], raw_pts[-1] = {'x': src['raw_x'], 'y': src['raw_y']}, {'x': tgt['raw_x'], 'y': tgt['raw_y']}
            
            scad_pts = [[p['x'], -p['y']] for p in raw_pts]
            edges.append({'points': scad_pts, 'src': src['shape'], 'tgt': tgt['shape'], 'label': label})
            
            all_x.extend([p[0] for p in scad_pts])
            all_y.extend([p[1] for p in scad_pts])

    # Calculate boundaries
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # --- NEW: FORCE SPINE CENTERING ---
    # Find the Start node's X coordinate
    main_spine_x = list(nodes.values())[0]['x']
    
    # Figure out the furthest distance any point reaches from that spine
    max_reach_x = max(abs(max_x - main_spine_x), abs(min_x - main_spine_x))
    
    # Force the bounding box to be perfectly symmetrical around the spine
    min_x = main_spine_x - max_reach_x
    max_x = main_spine_x + max_reach_x
    # ----------------------------------

    # --- CALCULATE THE Y-CUT TO AVOID NODES FOR THE 2-PART SPLIT  ---
    
    margin_x = 5  
    margin_y = 5  
    safe_margin_x = margin_x + (block_size / 2)
    safe_margin_y = margin_y + (block_size / 2)

    grid_spacing = min(
        (screen_width - (safe_margin_x * 2)) / max(1, (max_x - min_x)),
        (screen_height - (safe_margin_y * 2)) / max(1, (max_y - min_y))
    )
    
    y_offset = (screen_height / 2) - ((min_y + max_y) / 2 * grid_spacing)

    # Map the vertical footprint of every node using uniform scaling
    node_extents = []
    for n in nodes.values():
        actual_y = n['y'] * grid_spacing + y_offset 
        node_extents.append((actual_y - 12, actual_y + 12))
    
    node_extents.sort()

    # Find the largest empty vertical gap between nodes
    max_gap = 0
    cut_y = screen_height / 2.0
    for i in range(len(node_extents) - 1):
        gap = node_extents[i+1][0] - node_extents[i][1]
        if gap > max_gap and gap > 5: 
            max_gap = gap
            cut_y = node_extents[i][1] + (gap / 2.0)
    # =========================================================================

    # OPENSCAD TEMPLATE 
    scad = f"""// --- GLOBAL SETTINGS & CONSTANTS ---

use <braille.scad>; // library for the braille text
$fn = 64;
base_width = {screen_width};
base_height = {screen_height};
base_thickness = 2;
rounding_radius = 1; 


// Hardware dimensions
margin_top = {margin_top};
margin_bottom = {margin_bottom};
margin_left = {margin_left};
margin_right = {margin_right};


// Calculate total physical size of the tablet
//tablet_actual_width = base_width + margin_left + margin_right + 1;
//tablet_actual_height = base_height + margin_top + margin_bottom + 1;

//Dimensions of the actual tablet 
tablet_actual_width = {tablet_actual_width}; 
tablet_actual_height = {tablet_actual_height};


block_size = {block_size};   
outline_thickness = 1;
bb_h = 2; 
edge_radius = 1; 

shape_radius = (block_size / 2) + 1;
radius_diamond = (block_size / 2) * sqrt(2); 
radius_trapezoid = (block_size / 2) + (block_size * 0.15); 

arrow_length = 4;
arrow_width = 3.5;
margin_x = 5; 
margin_y = 5;

// --- SPACING ---
min_x = {min_x}; max_x = {max_x};
min_y = {min_y}; max_y = {max_y};

safe_margin_x = {safe_margin_x};
safe_margin_y = {safe_margin_y};

// Same uniform calculation is used internally by OpenSCAD
grid_spacing = {grid_spacing};
x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing);
function scale_p(p) = [p[0] * grid_spacing + x_offset, p[1] * grid_spacing + y_offset];

// --- MODULES ---
module draw_shape(type) {{
    if (type == "circle") offset(r = rounding_radius) circle(d = block_size, $fn=64);
    else if (type == "trapezoid") offset(r = rounding_radius) polygon([[-block_size/2+(block_size*0.15), block_size/2], [block_size/2+(block_size*0.15), block_size/2], [block_size/2-(block_size*0.15), -block_size/2], [-block_size/2-(block_size*0.15), -block_size/2]]);
    else if (type == "diamond") offset(r = rounding_radius) rotate([0, 0, 45]) square([block_size, block_size], center=true);
    else offset(r = rounding_radius) square([block_size, block_size], center=true);
}}

module place_node(x, y, type, mode="wall") {{
    p = scale_p([x, y]);
    if (mode == "hole") {{
        translate([p[0], p[1], -1]) 
            linear_extrude(base_thickness + 2) 
                offset(delta=-outline_thickness) union() {{ draw_shape(type); }}
    }} else {{
        // Sunk 0.1mm into the baseplate to prevent "floating" geometry
        translate([p[0], p[1], base_thickness - 0.1]) {{
            difference() {{
                linear_extrude(bb_h + 0.1) union() {{ draw_shape(type); }}
                translate([0, 0, -0.1]) 
                    linear_extrude(bb_h + 1) 
                        offset(delta=-outline_thickness) union() {{ draw_shape(type); }}
            }}
        }}
    }}
}}

// --- EDGE ROUTING MODULES ---
module edge_segment(p1, p2, is_start=false, is_end=false, src="square", tgt="square") {{
    p1s = scale_p(p1); p2s = scale_p(p2);
    dx = p2s[0] - p1s[0]; dy = p2s[1] - p1s[1];
    dist = sqrt(dx*dx + dy*dy); angle = atan2(dy, dx);
    sg = is_start ? ((src == "diamond" ? radius_diamond + 2 : shape_radius + 1)) : 0;
    eg = is_end ? ((tgt == "diamond" ? radius_diamond + 2 : shape_radius + 1) + arrow_length) : 0;
    if (dist - sg - eg > 0) translate([p1s[0] + cos(angle)*sg, p1s[1] + sin(angle)*sg, base_thickness]) rotate([0, 90, angle]) cylinder(h = dist - sg - eg, r = edge_radius, $fn=24);
}}

module edge_elbow(p) {{ 
    v = scale_p(p); 
    // Sunk slightly to ensure safe 3D printing
    translate([v[0], v[1], base_thickness - 0.1]) sphere(r = edge_radius, $fn=32); 
}}

module edge_arrow(p1, p2, tgt="square") {{
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    gd = (tgt == "diamond") ? radius_diamond + 2 : shape_radius + 1;
    // Sunk 0.1mm into baseplate
    translate([p2s[0] - cos(angle)*gd, p2s[1] - sin(angle)*gd, base_thickness - 0.1]) 
        rotate([0, 0, angle]) 
            linear_extrude(height = edge_radius + 0.1) 
                polygon(points=[[0, 0], [-arrow_length, -arrow_width / 2], [-arrow_length, arrow_width / 2]]);
}}

module edge_label(p1, p2, text_val) {{
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    adj_angle = (angle > 90 || angle < -90) ? angle + 180 : angle; 
    // Sunk 0.1mm into baseplate
    translate([(p1s[0] + p2s[0])/2 - sin(angle)*5, (p1s[1] + p2s[1])/2 + cos(angle)*5, base_thickness - 0.1])
        rotate([0, 0, adj_angle]) 
            linear_extrude(height=1.1) 
                text(text_val, size=4, spacing=1.5, valign="center", halign="center");
}}

// =========================================================================

module full_mask() {{
    union() {{
        difference() {{
            translate([-margin_left, -margin_bottom, 0])
                cube([tablet_actual_width, tablet_actual_height, base_thickness]);


            // --- MENU ACCESS HOLE ---
            translate([{menu_x} - {menu_radius}, {menu_y} - {menu_radius}, -1])
                cube([{menu_radius * 2}, {menu_radius * 2}, base_thickness + 2]);
"""
    # CORE SCAD SCRIPT
    scad_lines = [scad]

    # Holes
    for n in nodes.values():
        scad_lines.append(f"            place_node({n['x']}, {n['y']}, \"{n['shape']}\", \"hole\");")

    scad_lines.append("        }\n")

    # Walls
    for n in nodes.values():
        scad_lines.append(f"        place_node({n['x']}, {n['y']}, \"{n['shape']}\", \"wall\");")

    # Edges
    for e in edges:
        pts = e['points']
        for i in range(len(pts) - 1):
            is_start, is_end = ("true" if i == 0 else "false"), ("true" if i == len(pts) - 2 else "false")
            scad_lines.append(f"        edge_segment({pts[i]}, {pts[i+1]}, {is_start}, {is_end}, \"{e['src']}\", \"{e['tgt']}\");")
            if i > 0: scad_lines.append(f"        edge_elbow({pts[i]});")
        scad_lines.append(f"        edge_arrow({pts[-2]}, {pts[-1]}, \"{e['tgt']}\");")

    # Braille Title
    scad_lines.append("        // --- TACTILE TITLE ---")
    scad_lines.append("        translate([-margin_left + 10, base_height + margin_top - 10, base_thickness])")
    scad_lines.append(f"            braille(\"{board_title}\");")

    scad_lines.append("    }")
    scad_lines.append("}\n")
    

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

 # -------------------------------------------------
 # Bottom Part

    part1_scad = core_scad + f"""
// RENDER PART 1 (BOTTOM)
intersection() {{
    full_mask();
    translate([0, 0, -10]) linear_extrude(50) {{
        union() {{
            // Keep everything below the cut line
            translate([-500, -500]) square([1000, 500 + {cut_y}]);
            
            // Add two Rivets anchored to the outer edges
            translate([{left_peg_x}, {cut_y}]) puzzle_tab_shape(0);
            translate([{right_peg_x}, {cut_y}]) puzzle_tab_shape(0);
        }}
    }}
}}
"""
    file1 = base_scad_filepath.replace('.scad', '_lower.scad')
    with open(file1, 'w') as f: f.write(part1_scad)
    print(f"Successfully generated: {file1}")


    # -------------------------------------------------------------------------
    # Top Part
    
    part2_scad = core_scad + f"""
// RENDER PART 2 (TOP)
intersection() {{
    full_mask();
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
    file2 = base_scad_filepath.replace('.scad', '_upper.scad')
    with open(file2, 'w') as f: f.write(part2_scad)
    print(f"Successfully generated: {file2}")

    
    
    # -------------------------------------------------------------------------
    # Full Board

    part3_scad = core_scad + """
// RENDER FULL PREASSEMBLED BOARD
full_mask();
"""
    file3 = base_scad_filepath.replace('.scad', '_full.scad')
    with open(file3, 'w') as f: f.write(part3_scad)
    print(f"Successfully generated: {file3}")