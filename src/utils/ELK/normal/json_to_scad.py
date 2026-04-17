import json

def generate_scad(json_filepath, scad_filepath):
    # 1. LOAD & PARSE DATA
    with open(json_filepath, 'r') as file:
        data = json.load(file)

    # Store nodes in a dictionary keyed by ID for easy access later
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
    # Track all coordinates (nodes and edge bends) to calculate the bounding box
    all_x = [n['x'] for n in nodes.values()]
    all_y = [n['y'] for n in nodes.values()]

    for e in data.get('edges', []):
        src, tgt = nodes[e['source']], nodes[e['target']]
        label = e.get('labels', [{'text': None}])[0]['text'] if e.get('labels') else None

        for section in e.get('sections', []):
            raw_pts = [section['startPoint']] + section.get('bendPoints', []) + [section['endPoint']]
            # Snap ends exactly to node centers
            raw_pts[0], raw_pts[-1] = {'x': src['raw_x'], 'y': src['raw_y']}, {'x': tgt['raw_x'], 'y': tgt['raw_y']}
            
            scad_pts = [[p['x'], -p['y']] for p in raw_pts]
            edges.append({'points': scad_pts, 'src': src['shape'], 'tgt': tgt['shape'], 'label': label})
            
            # Add edge points to boundary tracking
            all_x.extend([p[0] for p in scad_pts])
            all_y.extend([p[1] for p in scad_pts])

    # Calculate boundaries
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # 2. OPENSCAD TEMPLATE (Notice all double brackets {{ }} for OpenSCAD logic)
    scad = f"""// --- GLOBAL SETTINGS & CONSTANTS ---
$fn = 64;
base_width = 135;
base_height = 217;
base_thickness = 1.5;
rounding_radius = 1; 

block_size = 17;   
outline_thickness = 1;
bb_h = 2; 
edge_radius = 1; 

shape_radius = (block_size / 2) + 1;
radius_diamond = (block_size / 2) * sqrt(2); 
radius_trapezoid = (block_size / 2) + (block_size * 0.15); 

arrow_length = 4;
arrow_width = 3.5;
margin_x = 14.115;
margin_y = 18.325;

// --- DYNAMIC GRID & SPACING ---
min_x = {min_x}; max_x = {max_x};
min_y = {min_y}; max_y = {max_y};

safe_margin_x = margin_x + (block_size / 2);
safe_margin_y = margin_y + (block_size / 2);
grid_spacing = min((base_width - (safe_margin_x * 2)) / max(1, (max_x - min_x)), 
                   (base_height - (safe_margin_y * 2)) / max(1, (max_y - min_y)));
                
x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing);
function scale_p(p) = [p[0] * grid_spacing + x_offset, p[1] * grid_spacing + y_offset];

// --- SOLID PRIMITIVES & HELPER MODULES ---
module draw_shape(type) {{
    if (type == "circle") circle(d = block_size, $fn=64);
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

// --- TOP LEVEL RENDERING ---
union() {{
    difference() {{
        cube([base_width, base_height, base_thickness]);
"""
    # 3. BUILD THE SCAD SCRIPT
    scad_lines = [scad]

    # Holes
    for n in nodes.values():
        scad_lines.append(f"        place_node({n['x']}, {n['y']}, \"{n['shape']}\", \"hole\");")
    scad_lines.append("    }\n")

    # Raised Walls
    for n in nodes.values():
        scad_lines.append(f"    place_node({n['x']}, {n['y']}, \"{n['shape']}\", \"wall\");")

    # Edges
    for e in edges:
        pts = e['points']
        for i in range(len(pts) - 1):
            is_start, is_end = ("true" if i == 0 else "false"), ("true" if i == len(pts) - 2 else "false")
            scad_lines.append(f"    edge_segment({pts[i]}, {pts[i+1]}, {is_start}, {is_end}, \"{e['src']}\", \"{e['tgt']}\");")
            if i > 0: scad_lines.append(f"    edge_elbow({pts[i]});")
        scad_lines.append(f"    edge_arrow({pts[-2]}, {pts[-1]}, \"{e['tgt']}\");")
        
        if e['label']:
            longest = max(zip(pts[:-1], pts[1:]), key=lambda seg: (seg[1][0]-seg[0][0])**2 + (seg[1][1]-seg[0][1])**2)
            scad_lines.append(f"    edge_label({longest[0]}, {longest[1]}, \"{e['label']}\");")

    scad_lines.append("}")

    # 4. SAVE FILE
    with open(scad_filepath, 'w') as f:
        f.write("\n".join(scad_lines))
        
    print(f"Successfully generated final OpenSCAD file: {scad_filepath}")

generate_scad('output_coordinates.json', 'flowchart.scad')