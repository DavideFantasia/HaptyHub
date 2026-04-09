import json


# In order to modify the dimensions of the component of the flowchart, you can adjust the following constants in the generated OpenSCAD file:
# - `base_width` and `base_height`: These control the overall size of the baseplate. You can set these to 130 and 200 respectively for a 130x200mm base.
# - `block_size`: This controls the size of the building blocks (circles, squares, diamonds, trapezoids). Adjust this to make the shapes larger or smaller.
# - `outline_thickness`: This controls how thick the raised walls of the shapes are. Increasing this will make the walls thicker and the holes smaller, while decreasing it will do the opposite.
# - `edge_radius`: This controls how thick the pipes are. Adjust this to make the pipes wider or narrower.
# - `arrow_length` and `arrow_width`: These control the size of the arrowheads at the end of each edge. Adjust these to make the arrows larger or smaller.
# - `bb_h`: This controls how tall the raised building blocks are. Adjust this to make the blocks taller or shorter.
# - `grid_spacing`: the number after base_width and base_height in the calculation determines how much margin u leave around the edges of the layout. Increasing the 20 to a larger number will create more space around the edges, while decreasing it will allow the layout to stretch closer to the edges of the baseplate.


def generate_scad(json_filepath, scad_filepath):
    # ---------------------------------------------------------
    # STEP 1: LOAD THE ELK DATA
    # ---------------------------------------------------------
    with open(json_filepath, 'r') as file:
        data = json.load(file)

    nodes = []
    edges = []
    
    # We track the extreme edges of the layout to calculate the bounding box.
    # This ensures we know exactly how wide and tall the ELK layout is so we 
    # can shrink or stretch it to fit your 130x200mm baseplate.
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    # ---------------------------------------------------------
    # STEP 2: PARSE THE NODES (BUILDING BLOCKS)
    # ---------------------------------------------------------
    for node in data.get('children', []):
        shape = node.get('myCustomShape', 'square')
        
        # ELK gives us the "Top-Left" corner of the invisible bounding box.
        # OpenSCAD draws from the "Center". So we add half the width/height.
        raw_cx = node['x'] + (node['width'] / 2.0)
        raw_cy = node['y'] + (node['height'] / 2.0)
        
        # ELK's Y-axis goes DOWN. OpenSCAD's Y-axis goes UP.
        # We invert the Y coordinate here so the flowchart doesn't print upside down.
        scad_cx = raw_cx
        scad_cy = -raw_cy
        
        # Save both the raw (for pipe routing) and SCAD (for boundaries) coordinates
        nodes.append({
            'id': node['id'], 'shape': shape, 
            'x': scad_cx, 'y': scad_cy, 
            'raw_x': raw_cx, 'raw_y': raw_cy
        })
        
        # Update our layout boundaries
        min_x = min(min_x, scad_cx)
        max_x = max(max_x, scad_cx)
        min_y = min(min_y, scad_cy)
        max_y = max(max_y, scad_cy)

    # ---------------------------------------------------------
    # STEP 3: PARSE THE EDGES (PIPES AND ARROWS)
    # ---------------------------------------------------------
    for edge in data.get('edges', []):
        # Find which nodes this edge connects
        source_node = next(n for n in nodes if n['id'] == edge['source'])
        target_node = next(n for n in nodes if n['id'] == edge['target'])
        
        # Grab the text label (e.g., "Yes", "No") if it exists
        labels = edge.get('labels', [])
        label_text = labels[0]['text'] if labels else None

        for section in edge.get('sections', []):
            # Combine the start point, the 90-degree corners, and the end point into one list
            raw_pts = [section['startPoint']] + section.get('bendPoints', []) + [section['endPoint']]
            
            # CRITICAL FIX: Overwrite the start/end points with the exact node centers.
            # ELK stops the line at the invisible box wall. By forcing the line to the true center,
            # OpenSCAD can use its own shape_radius math to trim the pipe perfectly to the physical shape.
            raw_pts[0] = {'x': source_node['raw_x'], 'y': source_node['raw_y']}
            raw_pts[-1] = {'x': target_node['raw_x'], 'y': target_node['raw_y']}
            
            # Convert all pipe coordinates to OpenSCAD's inverted Y-axis
            scad_pts = []
            for p in raw_pts:
                px = p['x']
                py = -p['y']
                scad_pts.append([px, py])
                
                # We also check the pipe corners against our boundaries so the elbows don't fall off the base
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_y = min(min_y, py)
                max_y = max(max_y, py)
                
            edges.append({
                'points': scad_pts,
                'source_shape': source_node['shape'],
                'target_shape': target_node['shape'],
                'label': label_text
            })

    # ---------------------------------------------------------
    # STEP 4: GENERATE THE OPENSCAD TEXT
    # ---------------------------------------------------------
    scad = []
    
    # Write the header and physical dimensions
    scad.append("""// --- GLOBAL SETTINGS & CONSTANTS ---
$fn = 50;
base_width = 148;
base_height = 236;
base_thickness = 3;

block_size = 15;
radius_circle = 7.5;
radius_square = 7.5;

// AUTOMATIC MATH: The pointy corner of a square rotated 45 degrees is (size/2) * sqrt(2)
radius_diamond = (block_size / 2) * sqrt(2); 
radius_trapezoid = 10;

outline_thickness = 1;
bb_h = 3;
edge_radius = 1.25;
shape_radius = (block_size / 2) + 1; // Standard +1mm gap to prevent overlapping
arrow_length = 4;
arrow_width = 4;
margin = 10;

// --- DYNAMIC GRID & SPACING ---""")
    
    # Write the layout boundaries we calculated in Python into SCAD
    scad.append(f"min_x = {min_x}; max_x = {max_x};")
    scad.append(f"min_y = {min_y}; max_y = {max_y};")
    
    # This OpenSCAD math calculates exactly how much to scale and shift the ELK coordinates
    # so they fit perfectly centered on the 130x200 baseplate with a 10mm margin.
    scad.append("""
grid_spacing = min((base_width - (margin * 2)) / max(1, (max_x - min_x)), 
                   (base_height - (margin * 2)) / max(1, (max_y - min_y)));

x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing);

// A helper function that scales and shifts every single coordinate automatically
function scale_p(p) = [p[0] * grid_spacing + x_offset, p[1] * grid_spacing + y_offset];

// --- SOLID PRIMITIVES ---
// These are the base 2D shapes used for both the raised walls and the hollow holes
module solid_circle() { circle(d = block_size, $fn=64); }
module solid_trapezoid() { slant = block_size * 0.15; polygon([[-block_size/2+slant, block_size/2], [block_size/2+slant, block_size/2], [block_size/2-slant, -block_size/2], [-block_size/2-slant, -block_size/2]]); }
module solid_diamond() { rotate([0, 0, 45]) square([block_size, block_size], center=true); }
module solid_square() { square([block_size, block_size], center=true); }

// --- EDGE ROUTING MODULES ---
// Draws a single pipe segment. It checks if it's touching a shape, and if so, trims its own length using 'start_gap' or 'end_gap'.
module edge_segment_direct(p1, p2, is_start=false, is_end=false, source_shape_type="square", target_shape_type="square") {
    p1s = scale_p(p1); 
    p2s = scale_p(p2);
    dx = p2s[0] - p1s[0]; 
    dy = p2s[1] - p1s[1];
    dist = sqrt(dx*dx + dy*dy); 
    angle = atan2(dy, dx);
    
    start_gap_dist = (source_shape_type == "diamond") ? (radius_diamond + 1) : shape_radius;
    start_gap = is_start ? start_gap_dist : 0;
    
    end_gap_dist = (target_shape_type == "diamond") ? (radius_diamond + 1) : shape_radius;
    end_gap = is_end ? (end_gap_dist + arrow_length) : 0;
    
    len = dist - start_gap - end_gap;
    if (len > 0) {
        translate([p1s[0] + cos(angle)*start_gap, p1s[1] + sin(angle)*start_gap, base_thickness])
            rotate([0, 90, angle]) 
                cylinder(h = len, r = edge_radius, $fn=24);
    }
}

// Drops a small sphere at 90-degree turns to make the outside corner look perfectly rounded
module edge_elbow_sphere(p) {
    v = scale_p(p);
    translate([v[0], v[1], base_thickness]) sphere(r = edge_radius, $fn=32);
}

// Draws the triangle arrowhead, pulling it back by gap_dist so its tip just kisses the shape outline
module edge_arrow_triangle(p1, p2, target_shape_type="square") {
    p1s = scale_p(p1);
    p2s = scale_p(p2);
    dx = p2s[0] - p1s[0];
    dy = p2s[1] - p1s[1];
    angle = atan2(dy, dx);
    dist = sqrt(dx*dx + dy*dy);
    if(dist > 0) {
        ux = dx / dist;
        uy = dy / dist;
        
        gap_dist = (target_shape_type == "diamond") ? (radius_diamond + 1) : shape_radius;
        tip_x = p2s[0] - ux * gap_dist;
        tip_y = p2s[1] - uy * gap_dist;

        translate([tip_x, tip_y, base_thickness])
            rotate([0, 0, angle])
                linear_extrude(height = edge_radius)
                    polygon(points=[[0, 0], [-arrow_length, -arrow_width / 2], [-arrow_length,  arrow_width / 2]]);
    }
}

// Finds the exact middle of an edge and drops the text label slightly to the side
module edge_weight_label(p1, p2, label_text) {
    p1s = scale_p(p1);
    p2s = scale_p(p2);
    mid_x = (p1s[0] + p2s[0]) / 2;
    mid_y = (p1s[1] + p2s[1]) / 2;
    dx = p2s[0] - p1s[0];
    dy = p2s[1] - p1s[1];
    angle = atan2(dy, dx);
    
    adj_angle = (angle > 90 || angle < -90) ? angle + 180 : angle; // Keeps text right-side up
    ox = -sin(angle) * 5; // 5mm offset
    oy = cos(angle) * 5;

    translate([mid_x + ox, mid_y + oy, 3])
        rotate([0, 0, adj_angle])
            linear_extrude(height = 1)
                text(label_text, size=4, spacing=1.5, valign="center", halign="center");
}

// --- TOP LEVEL RENDERING ---
union() {
    // SECTION 1: THE BASE
    difference() {
        translate([0, 0, 0]) cube([base_width, base_height, base_thickness], center=false);
        
        // Loop to cut holes through the base floor
""")
    # ---------------------------------------------------------
    # WRITE HOLE CUTTERS
    # ---------------------------------------------------------
    for node in nodes:
        shape_call = f"solid_{node['shape']}()"
        scad.append(f"        translate([scale_p([{node['x']}, {node['y']}])[0], scale_p([{node['x']}, {node['y']}])[1], -1]) linear_extrude(base_thickness + 2) offset(delta=-outline_thickness) {shape_call};")
    
    scad.append("""    }
    
    // SECTION 2: RAISED BUILDING BLOCKS
""")
    
    # ---------------------------------------------------------
    # WRITE RAISED WALLS
    # ---------------------------------------------------------
    for node in nodes:
        shape_call = f"solid_{node['shape']}()"
        scad.append("    difference() {")
        scad.append(f"        translate([scale_p([{node['x']}, {node['y']}])[0], scale_p([{node['x']}, {node['y']}])[1], base_thickness]) linear_extrude(bb_h) {shape_call};")
        scad.append(f"        translate([scale_p([{node['x']}, {node['y']}])[0], scale_p([{node['x']}, {node['y']}])[1], base_thickness - 0.1]) linear_extrude(bb_h + 1) offset(delta=-outline_thickness) {shape_call};")
        scad.append("    }")

    scad.append("\n    // SECTION 3: EDGES, ARROWHEADS, & LABELS")
    
    # ---------------------------------------------------------
    # WRITE EDGES AND PIPES
    # ---------------------------------------------------------
    for edge in edges:
        pts = edge['points']
        source = edge['source_shape']
        target = edge['target_shape']
        
        longest_dist = -1
        longest_segment = None

        # Loop through coordinate pairs (A->B, B->C) to draw segments
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i+1]
            is_start = "true" if i == 0 else "false"
            is_end = "true" if i == len(pts) - 2 else "false"
            
            # Draw the straight line
            scad.append(f"    edge_segment_direct({p1}, {p2}, {is_start}, {is_end}, \"{source}\", \"{target}\");")
            
            # If we are past the first coordinate, draw a round corner joint
            if i > 0:
                scad.append(f"    edge_elbow_sphere({p1});")
                
            # Figure out which straight segment is the longest so we know where to put the text
            dist_sq = (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2
            if dist_sq > longest_dist:
                longest_dist = dist_sq
                longest_segment = (p1, p2)

        # Draw the arrowhead on the very last segment
        scad.append(f"    edge_arrow_triangle({pts[-2]}, {pts[-1]}, \"{target}\");")
        
        # Draw the text label next to the longest segment
        if edge['label'] and longest_segment:
            scad.append(f"    edge_weight_label({longest_segment[0]}, {longest_segment[1]}, \"{edge['label']}\");")

    scad.append("}") # Close the union block

    # Save to file
    with open(scad_filepath, 'w') as f:
        f.write("\n".join(scad))
        
    print(f"Successfully generated final OpenSCAD file: {scad_filepath}")


generate_scad('output_coordinates.json', 'rigid_flowchart.scad')
