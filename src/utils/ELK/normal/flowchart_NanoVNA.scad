// --- GLOBAL SETTINGS ---
$fn = 64;
base_width = 135;
base_height = 217;
base_thickness = 3;
relief_depth = 1.5; 

block_size = 12.5;   
post_size = 3;      // Size of the stability cube
edge_radius = 1; 
shape_radius = (block_size / 2); 

gap = 1.0; 
arrow_length = 4;
arrow_width = 3.5;
margin_x = 14.115;
margin_y = 18.325;

// --- DYNAMIC GRID ---
min_x = 42.0; max_x = 152;
min_y = -702.0; max_y = -32.0;

safe_margin_x = margin_x + (block_size / 2);
safe_margin_y = margin_y + (block_size / 2);
grid_spacing = min((base_width - (safe_margin_x * 2)) / max(1, (max_x - min_x)), 
                   (base_height - (safe_margin_y * 2)) / max(1, (max_y - min_y)));
                
x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing);

function scale_p(p) = [p[0] * grid_spacing + x_offset, p[1] * grid_spacing + y_offset];

// --- MODULES ---
module node_relief(x, y) {
    p = scale_p([x, y]);
    translate([p[0], p[1], base_thickness - relief_depth])
        cylinder(h = relief_depth + 0.1, d = block_size);
}

module node_post(x, y) {
    p = scale_p([x, y]);
    // Start at the relief floor (3 - 1.5 = 1.5mm)
    // Cube height is 3mm
    // Result: Top of post is at Z = 4.5mm (1.5mm higher than the base)
    translate([p[0] - post_size/2, p[1] - post_size/2, base_thickness - relief_depth])
        cube([post_size, post_size, 3]);
}


module edge_segment(p1, p2, is_start=false, is_end=false) {
    p1s = scale_p(p1); p2s = scale_p(p2);
    dx = p2s[0] - p1s[0]; dy = p2s[1] - p1s[1];
    dist = sqrt(dx*dx + dy*dy); angle = atan2(dy, dx);
    sg = is_start ? shape_radius + gap : 0;
    eg = is_end ? shape_radius + arrow_length + gap : 0;
    if (dist - sg - eg > 0) 
        translate([p1s[0] + cos(angle)*sg, p1s[1] + sin(angle)*sg, base_thickness]) 
            rotate([0, 90, angle]) 
                cylinder(h = dist - sg - eg + 0.1, r = edge_radius, $fn=24);
}

module edge_elbow(p) { 
    v = scale_p(p); 
    translate([v[0], v[1], base_thickness]) sphere(r = edge_radius, $fn=32); 
}

module edge_arrow(p1, p2) {
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    translate([p2s[0] - cos(angle)*(shape_radius+gap), p2s[1] - sin(angle)*(shape_radius+gap), base_thickness]) 
        rotate([0, 0, angle]) 
            linear_extrude(height = edge_radius) 
                polygon(points=[[0, 0], [-arrow_length , -arrow_width/2], [-arrow_length, arrow_width/2]]);
}

module edge_label(p1, p2, text_val) {
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    adj_angle = (angle > 90 || angle < -90) ? angle + 180 : angle; 
    translate([(p1s[0] + p2s[0])/2 - sin(angle)*5, (p1s[1] + p2s[1])/2 + cos(angle)*5, base_thickness - 0.1])
        rotate([0, 0, adj_angle]) 
            linear_extrude(height=1.1) 
                text(text_val, size=4, spacing=1.5, valign="center", halign="center");
}

// --- RENDERING ---
union() {
    difference() {
        cube([base_width, base_height, base_thickness]);

        node_relief(42.0, -32.0);
        node_relief(42.0, -152.0);
        node_relief(42.0, -282.0);
        node_relief(42.0, -497.0);
        node_relief(42.0, -702.0);
    } // End difference
    node_post(42.0, -32.0);
    node_post(42.0, -152.0);
    node_post(42.0, -282.0);
    node_post(42.0, -497.0);
    node_post(42.0, -702.0);
    edge_segment([42.0, -32.0], [42.0, -152.0], true, true);
    edge_arrow([42.0, -32.0], [42.0, -152.0]);
    edge_segment([42.0, -152.0], [42.0, -282.0], true, true);
    edge_arrow([42.0, -152.0], [42.0, -282.0]);
    edge_segment([42.0, -282.0], [42.0, -497.0], true, true);
    edge_arrow([42.0, -282.0], [42.0, -497.0]);
    edge_label([42.0, -282.0], [42.0, -497.0], "Yes");
    edge_segment([42.0, -282.0], [152, -282], true, false);
    edge_segment([152, -282], [152, -602], false, false);
    edge_elbow([152, -282]);
    edge_segment([152, -602], [42, -602], false, false);
    edge_elbow([152, -602]);
    edge_segment([42, -602], [42.0, -702.0], false, true);
    edge_elbow([42, -602]);
    edge_arrow([42, -602], [42.0, -702.0]);
    edge_label([42.0, -282.0], [152, -282], "No");
    edge_segment([42.0, -497.0], [42.0, -702.0], true, true);
    edge_arrow([42.0, -497.0], [42.0, -702.0]);
}